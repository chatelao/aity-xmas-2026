# ==============================================================================
# aity-xmas-2026 | CircuitPython Show-Firmware (10+2 Baeume, 12x60 = 720 LEDs)
# - Automatische Koordinator-Arbitrage via ESP-NOW
# - Wi-Fi AP + Captive Portal (DNS Port 53 + adafruit_httpserver Port 80)
# - 6-Akt / 15-Minuten-3D-Show (stateless, weltweit 3D-koordiniert)
# - Synchrone Mehrstimmen-Musik via synthio + audiomixer (I2S / PWM Fallback)
# ==============================================================================

import gc
import json
import math
import os
import struct
import time

import audiomixer
import board
import espnow
import neopixel
import socketpool
import synthio
import wifi
from adafruit_httpserver import GET, POST, Redirect, Request, Response, Server

# ------------------------------------------------------------------------------
# 1. HARDWARE- & ENSEMBLE-KONFIGURATION (an eigenes Board anpassen!)
# ------------------------------------------------------------------------------
NUM_LEDS = 60
LED_PIN = getattr(board, "D10", getattr(board, "IO18", None))
LED_BRIGHTNESS_HW = 1.0  # Dimmung/ABL erfolgt sauber per Software-Skalierung

# Audio-Pins (PCB-Lautsprecher LS101 an D0 per PWM, optional externer I2S-DAC)
USE_I2S_AUDIO = False
I2S_BCLK_PIN = getattr(board, "D6", getattr(board, "IO21", None))
I2S_LRCK_PIN = getattr(board, "D7", getattr(board, "IO22", None))
I2S_DATA_PIN = getattr(board, "D8", getattr(board, "IO23", None))
AUDIO_PWM_PIN = getattr(board, "D0", getattr(board, "A0", None))
AUDIO_SAMPLE_RATE = 22050
AUDIO_LATENCY_OFFSET_MS = 25  # Ausgleich fuer Audio-Mixer-Puffer

# Funk- & Arbitrage-Parameter
RADIO_CHANNEL = 6
AP_SSID = "XMAS-2026-SHOW"
AP_PASSWORD = ""  # Offen lassen fuer zuverlaessiges Smartphone-Captive-Portal
ELECTION_WINDOW_MS = 3500
COORDINATOR_TIMEOUT_MS = 4500
SYNC_INTERVAL_MS = 500
FRAME_INTERVAL_MS = 20  # 50 FPS Ziel fuer fluessige CircuitPython-Schleife

# Aufstellungsplan 10+2 Baeume (X_mm, Y_Base_mm, Z_mm, Hoehe_mm, Basis_Diam_mm, Dichte-Norm)
TREE_LAYOUT = {
    "T01": (-1050, 0, 360, 100, 65, 0.35),
    "T02": (-630, 0, 460, 100, 65, 0.35),
    "T03": (-210, 0, 520, 100, 65, 0.35),
    "T04": (210, 0, 520, 100, 65, 0.35),
    "T05": (630, 0, 460, 100, 65, 0.35),
    "T06": (1050, 0, 360, 100, 65, 0.35),
    "T07": (-840, 140, 140, 100, 65, 0.35),
    "T08": (-300, 140, 220, 100, 65, 0.35),
    "T09": (300, 140, 220, 100, 65, 0.35),
    "T10": (840, 140, 140, 100, 65, 0.35),
    "T11": (520, 0, -280, 850, 480, 1.00),
    "T12": (-420, 0, -220, 1050, 600, 1.00),
}

# Optional: MAC-Adresse -> TREE_ID Zuordnung (kleingeschrieben, ohne Doppelpunkte)
MAC_TO_TREE_ID = {
    # "aabbccddeeff": "T12",
}

# Prioritaet fuer Koordinator-Arbitrage (kleinere Zahl = hoehere Prioritaet)
COORDINATOR_PRIORITY = {
    "T12": 0,
    "T11": 1,
}


def get_tree_id():
    env_id = os.getenv("TREE_ID")
    if env_id in TREE_LAYOUT:
        return env_id
    mac_hex = "".join("%02x" % b for b in wifi.radio.mac_address)
    return MAC_TO_TREE_ID.get(mac_hex, "T01")


TREE_ID = get_tree_id()
TREE_CFG = TREE_LAYOUT[TREE_ID]
MY_MAC = bytes(wifi.radio.mac_address)
MY_PRIO = COORDINATOR_PRIORITY.get(TREE_ID, 10)
IS_HERO = TREE_ID in ("T11", "T12")


def now_ms():
    return time.monotonic_ns() // 1_000_000


# ------------------------------------------------------------------------------
# 2. GLOBALE 3D-VOXEL-KOORDINATEN (60 LEDs -> Weltkoordinaten in mm)
# ------------------------------------------------------------------------------
def build_world_coords():
    tx, ty_base, tz, h_mm, d_mm, _ = TREE_CFG
    r_base = d_mm / 2.0
    turns = 5.0  # Parametrische Kegelspirale (durch Repo-LUT ersetzbar)
    coords = []
    for i in range(NUM_LEDS):
        u = i / float(NUM_LEDS - 1)
        r = r_base * (1.0 - u)
        ang = u * turns * 2.0 * math.pi
        wx = int(tx + r * math.cos(ang))
        wy = int(ty_base + u * h_mm)
        wz = int(tz + r * math.sin(ang))
        coords.append((wx, wy, wz))
    return tuple(coords)


WORLD_COORDS = build_world_coords()
DENSITY_SCALE = TREE_CFG[5]

# Gamma-Lookup-Tabelle (gamma = 2.4) fuer weiche Dimmverlaeufe
GAMMA_LUT = bytes(int(((i / 255.0) ** 2.4) * 255.0 + 0.5) for i in range(256))

# ------------------------------------------------------------------------------
# 3. MUSIK-TIMELINE (6 AKTE = 364 TAKTE = 900.000 s) & SYNTHIO-SEQUENCER
# ------------------------------------------------------------------------------
# (act_id, name, start_ms, dur_ms, bpm, bars)
ACTS = (
    (1, "Akt 1: Erwachen & Puls", 0, 120_000, 72, 36),
    (2, "Akt 2: Geometrie & Linien", 120_000, 150_000, 112, 70),
    (3, "Akt 3: Wellen & Dialog", 270_000, 180_000, 96, 72),
    (4, "Akt 4: Polarlicht & Stille", 450_000, 150_000, 64, 40),
    (5, "Akt 5: Uhrwerk & Crescendo", 600_000, 180_000, 128, 96),
    (6, "Akt 6: Finale & Winterfrieden", 780_000, 120_000, 120, 60),  # 80s @120 + 40s @60
)
SHOW_TOTAL_MS = 900_000

# Kompakte mehrstimmige Phrasen pro Akt (8 Schritte/Takt = Achtel-Raster):
# (Lead-MIDI-Note oder None, Bass-MIDI-Note oder None)
PATTERNS = {
    1: ((62, None, 65, None, 69, None, 67, None), (38, None, None, None, None, None, None, None)),
    2: ((62, 65, 69, 74, 72, 69, 65, 62), (38, None, 50, None, 36, None, 48, None)),
    3: ((65, None, 69, 72, 67, None, 70, 74), (41, None, None, None, 43, None, None, None)),
    4: ((67, None, None, None, 70, None, 69, None), (43, None, None, None, 39, None, None, None)),
    5: ((74, 69, 65, 69, 74, 69, 65, 69), (38, 38, 50, 38, 36, 36, 48, 36)),
    6: ((74, None, 78, None, 81, None, 79, 78), (38, None, None, None, 45, None, None, None)),
}


class MusicEngine:
    def __init__(self):
        self.audio = None
        self.mixer = None
        self.synth = None
        self.pwm = None
        self.enabled = True
        self.volume = 0.35
        self.last_step_key = None
        self.active_notes = []
        self._init_audio()

    def _init_audio(self):
        try:
            if USE_I2S_AUDIO and I2S_BCLK_PIN and I2S_LRCK_PIN and I2S_DATA_PIN:
                import audiobusio

                self.audio = audiobusio.I2SOut(I2S_BCLK_PIN, I2S_LRCK_PIN, I2S_DATA_PIN)
            elif AUDIO_PWM_PIN:
                try:
                    import audiopwmio

                    self.audio = audiopwmio.PWMAudioOut(AUDIO_PWM_PIN)
                except Exception:
                    import pwmio

                    self.pwm = pwmio.PWMOut(
                        AUDIO_PWM_PIN, duty_cycle=0, frequency=440, variable_frequency=True
                    )
                    return
            else:
                return

            self.mixer = audiomixer.Mixer(
                voice_count=1,
                sample_rate=AUDIO_SAMPLE_RATE,
                channel_count=1,
                bits_per_sample=16,
                samples_signed=True,
                buffer_size=2048,
            )
            env = synthio.Envelope(
                attack_time=0.015,
                decay_time=0.18,
                sustain_level=0.35,
                release_time=0.22,
            )
            self.synth = synthio.Synthesizer(sample_rate=AUDIO_SAMPLE_RATE, envelope=env)
            self.audio.play(self.mixer)
            self.mixer.voice[0].play(self.synth)
            self.mixer.voice[0].level = self.volume
        except Exception as err:
            print("Audio-Init uebersprungen:", err)
            self.audio = None
            self.pwm = None

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))
        if self.mixer:
            self.mixer.voice[0].level = self.volume if self.enabled else 0.0
        elif self.pwm and (not self.enabled or self.volume <= 0.0):
            self.pwm.duty_cycle = 0

    def silence(self):
        if self.synth and self.active_notes:
            self.synth.release(self.active_notes)
            self.active_notes = []
        if self.pwm:
            self.pwm.duty_cycle = 0
        self.last_step_key = None

    def update(self, show_ms, playing, is_coordinator):
        if (not self.synth and not self.pwm) or not self.enabled or not playing:
            self.silence()
            return
        # Standardmaessig spielt der Koordinator (z. B. am PA/Lautsprecher);
        # falls jeder Baum eigene Lautsprecher hat, Bedingung entfernen.
        if not is_coordinator:
            return

        t_audio = max(0, show_ms - AUDIO_LATENCY_OFFSET_MS) % SHOW_TOTAL_MS
        act_id, bpm, local_ms = resolve_act(t_audio)
        # In Akt 6b (ab 860_000 ms) Tempo auf 60 BPM halbieren
        if t_audio >= 860_000:
            bpm = 60
            local_ms = t_audio - 860_000

        eighth_ms = 30_000.0 / bpm
        step_total = int(local_ms / eighth_ms)
        step_in_bar = step_total % 8
        key = (act_id, step_total)
        if key == self.last_step_key:
            return
        self.last_step_key = key

        lead_seq, bass_seq = PATTERNS[act_id]
        if self.pwm:
            note = lead_seq[step_in_bar]
            if note is not None and self.volume > 0.0:
                self.pwm.frequency = int(440.0 * (2.0 ** ((note - 69) / 12.0)))
                self.pwm.duty_cycle = int(32768 * self.volume)
            else:
                self.pwm.duty_cycle = 0
            return

        if self.active_notes:
            self.synth.release(self.active_notes)
            self.active_notes = []

        to_press = []
        if lead_seq[step_in_bar] is not None:
            to_press.append(synthio.Note(synthio.midi_to_hz(lead_seq[step_in_bar])))
        if bass_seq[step_in_bar] is not None:
            to_press.append(synthio.Note(synthio.midi_to_hz(bass_seq[step_in_bar])))
        if to_press:
            self.synth.press(to_press)
            self.active_notes = to_press


def resolve_act(t_ms):
    t = t_ms % SHOW_TOTAL_MS
    for act_id, _, start_ms, dur_ms, bpm, _ in ACTS:
        if start_ms <= t < start_ms + dur_ms:
            return act_id, bpm, t - start_ms
    return 1, 72, 0


# ------------------------------------------------------------------------------
# 4. ZUSTANDSLOSE 3D-ANIMATIONEN (ALLE 12 BAEUME IM GEMEINSAMEN WELT-RAUM)
# ------------------------------------------------------------------------------
pixels = neopixel.NeoPixel(
    LED_PIN, NUM_LEDS, brightness=LED_BRIGHTNESS_HW, auto_write=False, pixel_order=neopixel.GRB
)


def hsv_to_rgb(h, s, v):
    h = h % 1.0
    i = int(h * 6.0)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    m = i % 6
    if m == 0:
        r, g, b = v, t, p
    elif m == 1:
        r, g, b = q, v, p
    elif m == 2:
        r, g, b = p, v, t
    elif m == 3:
        r, g, b = p, q, v
    elif m == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return r, g, b


def render_frame(show_ms, master_dim, forced_act=0):
    t_s = (show_ms % SHOW_TOTAL_MS) / 1000.0
    act_id, bpm, local_ms = resolve_act(show_ms)
    if forced_act in (1, 2, 3, 4, 5, 6):
        act_id = forced_act
        bpm = ACTS[act_id - 1][4]

    beat = (local_ms / 1000.0) * (bpm / 60.0)
    beat_frac = beat - int(beat)
    pulse = math.exp(-4.5 * beat_frac)
    scale = master_dim * DENSITY_SCALE

    for idx in range(NUM_LEDS):
        wx, wy, wz = WORLD_COORDS[idx]
        r = g = b = 0.0

        if act_id == 1:
            # Akt 1: Erwachen & Puls (Gluehwuermchen auf T01-T10 -> Puls auf T11/T12)
            phase = (idx * 0.618 + wx * 0.013 + t_s * 0.9) % 1.0
            spark = max(0.0, math.sin(phase * math.pi) ** 8)
            if IS_HERO and local_ms < 90_000:
                spark = 0.0
            elif IS_HERO:
                spark = 0.6 * pulse if wy < 250 else 0.0
            amp = (0.35 * spark + 0.65 * pulse * (1.0 if local_ms > 60_000 else 0.2))
            r, g, b = 1.0 * amp, 0.52 * amp, 0.12 * amp

        elif act_id == 2:
            # Akt 2: Volumetrische 3D-Schnittebene & Doppelhelix durch alle 12 Baeume
            plane_d = 1100.0 * math.sin(t_s * 0.9)
            dist = abs((wx * 0.75 + wy * 0.45 + wz * 0.48) - plane_d)
            beam = max(0.0, 1.0 - dist / 140.0)
            helix = 0.5 + 0.5 * math.sin((wy * 0.015) - t_s * 3.5 + (wx * 0.004))
            r, g, b = hsv_to_rgb(0.55 + 0.08 * helix, 0.85, max(beam, 0.35 * helix))

        elif act_id == 3:
            # Akt 3: S-Welle im Vorfeld + Call-and-Response T11 (Blau) <-> T12 (Gold)
            wave_x = 1100.0 * math.sin(t_s * 1.4)
            dist_x = abs(wx - wave_x)
            trail = max(0.0, 1.0 - dist_x / 320.0)
            turn_gold = math.sin(t_s * 0.8) >= 0.0
            if TREE_ID == "T12":
                r, g, b = (1.0, 0.68, 0.15) if turn_gold else (0.08, 0.25, 0.45)
                amp = 0.85 * pulse if turn_gold else 0.25
            elif TREE_ID == "T11":
                r, g, b = (0.15, 0.65, 1.0) if not turn_gold else (0.35, 0.25, 0.08)
                amp = 0.85 * pulse if not turn_gold else 0.25
            else:
                r, g, b = (1.0, 0.65, 0.18) if turn_gold else (0.15, 0.68, 1.0)
                amp = trail * (0.4 + 0.6 * pulse)
            r, g, b = r * amp, g * amp, b * amp

        elif act_id == 4:
            # Akt 4: Polarlicht & Stille (~70% Negativraum + fallende Schneeflocken)
            aurora = math.sin(wx * 0.004 + t_s * 0.35) * math.cos(wz * 0.005 - t_s * 0.25)
            if aurora > 0.25:
                hue = 0.42 + 0.18 * math.sin(wx * 0.003 + t_s * 0.2)
                r, g, b = hsv_to_rgb(hue, 0.9, (aurora - 0.25) * 0.9)
            snow_y = (1050.0 - ((t_s * 260.0 + idx * 97.0) % 1150.0))
            if abs(wy - snow_y) < 35.0 and ((idx + int(t_s)) % 7 == 0):
                r, g, b = 0.95, 0.98, 1.0

        elif act_id == 5:
            # Akt 5: Sphaerische 3D-Schallwellen aus der Spitze von T12 (-420, 1050, -220)
            dx = wx - (-420)
            dy = wy - 1050
            dz = wz - (-220)
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            front = beat_frac * 2200.0
            ring = max(0.0, 1.0 - abs(dist - front) / 210.0)
            hue = 0.62 - 0.50 * ring
            r, g, b = hsv_to_rgb(hue, 0.95, max(ring, 0.15 * pulse))

        else:
            # Akt 6: Supernova-Wirbel -> sanftes Kerzenflackern (ab 860_000 ms)
            if (show_ms % SHOW_TOTAL_MS) < 860_000:
                ang = math.atan2(wz, wx) + wy * 0.006 - t_s * 4.0
                swirl = 0.5 + 0.5 * math.sin(ang * 2.0)
                r, g, b = hsv_to_rgb(0.08 + 0.06 * swirl, 0.75, 0.55 + 0.45 * pulse)
            else:
                flicker = 0.45 + 0.35 * math.sin(t_s * 7.3 + idx * 1.9 + wx * 0.02)
                amp = flicker * (0.35 if IS_HERO else 0.85)
                r, g, b = 1.0 * amp, 0.55 * amp, 0.15 * amp

        ri = GAMMA_LUT[min(255, max(0, int(r * scale * 255.0)))]
        gi = GAMMA_LUT[min(255, max(0, int(g * scale * 255.0)))]
        bi = GAMMA_LUT[min(255, max(0, int(b * scale * 255.0)))]
        pixels[idx] = (ri, gi, bi)

    pixels.show()


# ------------------------------------------------------------------------------
# 5. ESP-NOW FUNK- & ARBITRAGE-PROTOKOLL
# ------------------------------------------------------------------------------
MAGIC = b"AX26"
PKT_ELEC = 1
PKT_SYNC = 2
PKT_FMT = "<4sBBHQBBH"  # magic(4), type(1), prio(1), seq(2), show_ms(8), playing(1), forced_act(1), dim_u16(2) = 20B


def setup_espnow_broadcast(e_obj, prefer_ap_iface=False):
    while len(e_obj.peers) > 0:
        e_obj.peers.remove(e_obj.peers[0])
    configs = (
        [(RADIO_CHANNEL, 1), (0, 1), (0, 0), (RADIO_CHANNEL, 0)]
        if prefer_ap_iface
        else [(RADIO_CHANNEL, 0), (0, 0)]
    )
    for ch, iface in configs:
        try:
            peer = espnow.Peer(mac=b"\xff\xff\xff\xff\xff\xff", channel=ch, interface=iface)
            e_obj.peers.append(peer)
            return peer
        except Exception as err:
            print("ESP-NOW Peer Retry:", ch, iface, err)
    return None


def lock_radio_channel():
    wifi.radio.start_ap(" ", "", channel=RADIO_CHANNEL, max_connections=0)
    wifi.radio.stop_ap()


# ------------------------------------------------------------------------------
# 6. CAPTIVE PORTAL (DNS PORT 53 + HTTP SERVER PORT 80) FUER DEN KOORDINATOR
# ------------------------------------------------------------------------------
HTML_UI = """<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>aity-xmas-2026 Show</title><style>
body{font-family:system-ui,sans-serif;background:#0f172a;color:#f8fafc;margin:0;padding:16px}
.card{max-width:460px;margin:auto;background:#1e293b;border-radius:14px;padding:18px;box-shadow:0 10px 25px #0006}
h1{font-size:1.25rem;margin:0 0 8px;color:#38bdf8}.row{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
button{flex:1;min-width:90px;padding:10px;border:0;border-radius:8px;background:#0284c7;color:#fff;font-weight:600;cursor:pointer}
button.sec{background:#334155}button.act{background:#0f766e}input[type=range]{width:100%}
.meta{font-size:.85rem;color:#94a3b8;margin-top:8px}</style></head><body><div class="card">
<h1>aity-xmas-2026 | 10+2 Baum-Show</h1><div class="meta" id="st">Lade Status...</div>
<div class="row"><button onclick="cmd({playing:true})">Start / Play</button>
<button class="sec" onclick="cmd({playing:false})">Pause</button>
<button class="sec" onclick="cmd({show_ms:0,playing:true})">Neustart 00:00</button></div>
<div><label>Helligkeit</label><input type="range" min="10" max="100" value="70" onchange="cmd({dim:this.value/100})"></div>
<div><label>Musik-Lautstaerke</label><input type="range" min="0" max="100" value="35" onchange="cmd({vol:this.value/100})"></div>
<div class="row"><button class="act" onclick="cmd({act:0})">Auto-Show</button>
<button class="act" onclick="cmd({act:1})">Akt 1</button><button class="act" onclick="cmd({act:2})">Akt 2</button>
<button class="act" onclick="cmd({act:3})">Akt 3</button><button class="act" onclick="cmd({act:4})">Akt 4</button>
<button class="act" onclick="cmd({act:5})">Akt 5</button><button class="act" onclick="cmd({act:6})">Akt 6</button></div>
</div><script>
async function cmd(p){await fetch('/api/control',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});upd();}
async function upd(){const r=await fetch('/api/state');const s=await r.json();
const m=Math.floor(s.show_ms/60000),sec=Math.floor((s.show_ms%60000)/1000);
document.getElementById('st').textContent=`Koordinator: ${s.tree} | Zeit ${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')} | Akt ${s.act} | ${s.playing?'Aktiv':'Pause'}`;}
setInterval(upd,1200);upd();</script></body></html>"""


class CaptivePortal:
    def __init__(self, state, music):
        self.state = state
        self.music = music
        wifi.radio.start_ap(ssid=AP_SSID, password=AP_PASSWORD, channel=RADIO_CHANNEL)
        self.ap_ip = str(wifi.radio.ipv4_address_ap)
        self.ap_ip_bytes = bytes(wifi.radio.ipv4_address_ap.packed)
        self.pool = socketpool.SocketPool(wifi.radio)

        # Nicht-blockierender DNS-Server (Port 53) fuer Captive-Portal-Popup
        self.dns_sock = self.pool.socket(self.pool.AF_INET, self.pool.SOCK_DGRAM)
        self.dns_sock.bind(("0.0.0.0", 53))
        self.dns_sock.setblocking(False)
        self.dns_buf = bytearray(512)

        self.server = Server(self.pool, debug=False)
        self.server.socket_timeout = 0.02
        self._register_routes()
        self.server.start(self.ap_ip, port=80)
        print("Captive Portal aktiv auf http://%s (SSID: %s)" % (self.ap_ip, AP_SSID))

    def _register_routes(self):
        @self.server.route("/", GET)
        def index(request: Request):
            return Response(request, HTML_UI, content_type="text/html")

        # OS-Konnektivitaetspruefungen -> Redirect loest Captive-Portal-Anzeige aus
        for probe in (
            "/generate_204",
            "/gen_204",
            "/hotspot-detect.html",
            "/library/test/success.html",
            "/connecttest.txt",
            "/ncsi.txt",
            "/redirect",
        ):
            self.server.route(probe, GET)(lambda req: Redirect(req, "http://%s/" % self.ap_ip))

        @self.server.route("/api/state", GET)
        def api_state(request: Request):
            act_id, _, _ = resolve_act(self.state["show_ms"])
            payload = {
                "tree": TREE_ID,
                "show_ms": int(self.state["show_ms"]),
                "act": self.state["forced_act"] or act_id,
                "playing": self.state["playing"],
            }
            return Response(request, json.dumps(payload), content_type="application/json")

        @self.server.route("/api/control", POST)
        def api_control(request: Request):
            try:
                data = request.json()
            except Exception:
                data = {}
            if "playing" in data:
                self.state["playing"] = bool(data["playing"])
            if "show_ms" in data:
                self.state["show_ms"] = int(data["show_ms"]) % SHOW_TOTAL_MS
            if "act" in data:
                a = int(data["act"])
                self.state["forced_act"] = a
                if a in (1, 2, 3, 4, 5, 6):
                    self.state["show_ms"] = ACTS[a - 1][2]
            if "dim" in data:
                self.state["dim"] = max(0.05, min(1.0, float(data["dim"])))
            if "vol" in data:
                self.music.set_volume(float(data["vol"]))
            self.state["force_sync"] = True
            return Response(request, '{"ok":true}', content_type="application/json")

        @self.server.route("/....", GET)
        def catch_all(request: Request):
            return Redirect(request, "http://%s/" % self.ap_ip)

    def poll(self):
        # DNS-Anfragen ohne Blockierung beantworten
        for _ in range(4):
            try:
                n, addr = self.dns_sock.recvfrom_into(self.dns_buf)
            except OSError:
                break
            if n < 13:
                continue
            q_end = 12
            while q_end < n and self.dns_buf[q_end] != 0:
                q_end += self.dns_buf[q_end] + 1
            q_end += 5
            if q_end > n:
                continue
            resp = (
                bytes(self.dns_buf[0:2])
                + b"\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00"
                + bytes(self.dns_buf[12:q_end])
                + b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04"
                + self.ap_ip_bytes
            )
            try:
                self.dns_sock.sendto(resp, addr)
            except OSError:
                pass

        try:
            self.server.poll()
        except Exception:
            pass

    def stop(self):
        try:
            self.server.stop()
            self.dns_sock.close()
            wifi.radio.stop_ap()
        except Exception:
            pass


# ------------------------------------------------------------------------------
# 7. HAUPTSCHLEIFE: ARBITRAGE, TAKTSYNCHRONISATION & SHOW-AUSFUEHRUNG
# ------------------------------------------------------------------------------
def run_election(e_obj, peer):
    best = (MY_PRIO, MY_MAC)
    t_end = now_ms() + ELECTION_WINDOW_MS
    last_tx = 0
    while now_ms() < t_end:
        t = now_ms()
        if t - last_tx >= 400 and peer:
            pkt = struct.pack(PKT_FMT, MAGIC, PKT_ELEC, MY_PRIO, 0, 0, 1, 0, 0)
            try:
                e_obj.send(pkt, peer)
            except Exception:
                pass
            last_tx = t
        while e_obj:
            rx = e_obj.read()
            if rx and len(rx.msg) >= struct.calcsize(PKT_FMT):
                magic, ptype, prio, _, _, _, _, _ = struct.unpack(PKT_FMT, rx.msg[:20])
                if magic == MAGIC and ptype in (PKT_ELEC, PKT_SYNC):
                    cand = (prio, bytes(rx.mac))
                    if cand < best:
                        best = cand
        time.sleep(0.02)
    return best == (MY_PRIO, MY_MAC)


def main():
    lock_radio_channel()
    e_obj = espnow.ESPNow(buffer_size=526)
    bcast_peer = setup_espnow_broadcast(e_obj, prefer_ap_iface=False)

    is_coordinator = run_election(e_obj, bcast_peer)
    music = MusicEngine()
    state = {
        "show_ms": 0,
        "playing": True,
        "forced_act": 0,
        "dim": 0.70,
        "force_sync": False,
    }

    portal = None
    if is_coordinator:
        portal = CaptivePortal(state, music)
        bcast_peer = setup_espnow_broadcast(e_obj, prefer_ap_iface=True)

    gc.collect()
    seq = 0
    last_tick = now_ms()
    last_sync_tx = 0
    last_sync_rx = now_ms()
    last_frame = 0

    while True:
        t = now_ms()
        dt = t - last_tick
        last_tick = t
        if state["playing"]:
            state["show_ms"] = (state["show_ms"] + dt) % SHOW_TOTAL_MS

        if is_coordinator:
            if portal:
                portal.poll()
            if state["force_sync"] or (t - last_sync_tx >= SYNC_INTERVAL_MS):
                dim_u16 = int(state["dim"] * 65535)
                pkt = struct.pack(
                    PKT_FMT,
                    MAGIC,
                    PKT_SYNC,
                    MY_PRIO,
                    seq & 0xFFFF,
                    state["show_ms"],
                    1 if state["playing"] else 0,
                    state["forced_act"],
                    dim_u16,
                )
                if bcast_peer:
                    try:
                        e_obj.send(pkt, bcast_peer)
                    except Exception:
                        pass
                seq += 1
                last_sync_tx = t
                state["force_sync"] = False
        else:
            while e_obj:
                rx = e_obj.read()
                if rx and len(rx.msg) >= 20:
                    magic, ptype, prio, _, m_ms, m_play, m_act, dim_u16 = struct.unpack(
                        PKT_FMT, rx.msg[:20]
                    )
                    if magic == MAGIC and ptype == PKT_SYNC:
                        # Weiches Slewing bei kleinen Abweichungen, Sprung ab >15 ms
                        diff = m_ms - state["show_ms"]
                        if abs(diff) > 15:
                            state["show_ms"] = m_ms
                        else:
                            state["show_ms"] = (state["show_ms"] + int(diff * 0.25)) % SHOW_TOTAL_MS
                        state["playing"] = bool(m_play)
                        state["forced_act"] = m_act
                        state["dim"] = dim_u16 / 65535.0
                        last_sync_rx = t
            # Koordinator-Failover bei Verbindungsverlust
            if t - last_sync_rx > COORDINATOR_TIMEOUT_MS:
                if run_election(e_obj, bcast_peer):
                    is_coordinator = True
                    portal = CaptivePortal(state, music)
                    bcast_peer = setup_espnow_broadcast(e_obj, prefer_ap_iface=True)
                last_sync_rx = now_ms()

        music.update(state["show_ms"], state["playing"], is_coordinator)

        if t - last_frame >= FRAME_INTERVAL_MS:
            render_frame(state["show_ms"], state["dim"], state["forced_act"])
            last_frame = t

        time.sleep(0.002)


main()
