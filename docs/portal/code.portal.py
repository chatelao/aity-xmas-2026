# code.portal.py
# Zero-Install Wi-Fi Captive Portal Firmware for CircuitPython (Seeed Studio XIAO ESP32-C6)
# 100% feature parity with chatelao/android-xmas-tree-app and esp32c6-portal
#
# Dependencies on CIRCUITPY (/lib/):
#   - neopixel.mpy
#   - tannenbaum_layout.py
#   - tannenbaum_palettes.py
#   - /web_ui.html.gz (copied alongside code.py on root)
#
# Usage:
#   Copy this file as code.py and web_ui.html.gz to the root of your ESP32-C6.
#   Connect any phone/laptop to Wi-Fi "AITY-Xmas-Tree" -> http://192.168.4.1/ opens automatically.

import errno
import json
import math
import time
import board
import neopixel
import pwmio
import socketpool
import wifi

from tannenbaum_layout import (
    NUM_PIXELS,
    PIN_NEOPIXEL,
    PIXEL_COORDS,
    CENTER_TREE,
    POLAR_TREE,
    EPICENTERS,
    SEGMENTS,
    SEG_BOUGH_MID,
    VIRTUAL_SEGMENTS,
    TREE_TYPE_PCB,
    TREE_TYPE_HOLZ,
    MappedPixels,
    normalize_tree_type,
    build_distance_lut,
)
from tannenbaum_palettes import (
    PALETTES,
    PAL_FAIRY_LIGHT,
    render_twinkle_tree,
)

FIRMWARE_VERSION = "1.0.0-cp"
AP_SSID = "AITY-Xmas-Tree"
STATE_FILE = "/xmas_state.json"
PRESETS_FILE = "/xmas_presets.json"
WEB_UI_GZ_FILE = "/web_ui.html.gz"

# --- Captive Portal Probe URIs ---
PROBE_URIS = (
    "/generate_204",
    "/gen_204",
    "/hotspot-detect.html",
    "/library/test/success.html",
    "/connecttest.txt",
    "/ncsi.txt",
    "/redirect",
    "/fwlink",
    "/canonical.html",
    "/success.txt",
    "/mobile/status.php",
)

# --- RTTTL Melodies ---
RTTTL_SCORES = (
    "",
    "JingleBells:d=4,o=5,b=125:8g,8e,8d,c,2g,8g,8e,8d,c,2a,8a,8f,8e,d,2b,8g,8g,8f,8d,e",
    "WeWishYou:d=4,o=5,b=140:d,g,8g,8a,8g,8f#,e,c,e,a,8a,8b,8a,8g,f#,d,f#,b,8b,8c6,8b,8a,g,e,8d,8d,e,a,f#,2g",
    "SilentNight:d=4,o=5,b=90:4.g,8a,g,2.e,4.g,8a,g,2.e,2d6,2d6,2.b,2c6,2c6,2.g",
    "DeckTheHalls:d=4,o=5,b=140:4.g,8f,e,d,c,d,e,c,8d,8e,f,d,4.e,8d,c,b4,2c",
)

BASE_FREQS = {
    "c": 262, "c#": 277, "d": 294, "d#": 311, "e": 330,
    "f": 349, "f#": 370, "g": 392, "g#": 415, "a": 440,
    "a#": 466, "b": 494,
}

SEG_COLORS = (
    (0, 180, 255),
    (0, 255, 80),
    (120, 0, 255),
    (255, 0, 140),
    (255, 40, 0),
    (255, 180, 0),
)

DEFAULT_PRESETS = [
    {
        "id": "default-classic", "name": "Klassische Weihnachten",
        "pattern_id": 4, "palette_id": 0, "red": 255, "green": 60, "blue": 10,
        "brightness": 85, "speed": 45, "melody_id": 1, "volume": 70, "tempo": 100,
    },
    {
        "id": "default-rainbow", "name": "Regenbogen-Party",
        "pattern_id": 2, "palette_id": 0, "red": 0, "green": 255, "blue": 128,
        "brightness": 90, "speed": 75, "melody_id": 4, "volume": 75, "tempo": 110,
    },
    {
        "id": "default-silent-night", "name": "Gemütliche Stille Nacht",
        "pattern_id": 5, "palette_id": 0, "red": 255, "green": 200, "blue": 100,
        "brightness": 55, "speed": 30, "melody_id": 3, "volume": 50, "tempo": 95,
    },
]


def hsv_to_rgb(hue, val):
    if val <= 0:
        return (0, 0, 0)
    region = hue // 43
    rem = (hue - region * 43) * 6
    q = (val * (255 - rem)) >> 8
    t = (val * rem) >> 8
    if region == 0:
        return (val, t, 0)
    if region == 1:
        return (q, val, 0)
    if region == 2:
        return (0, val, t)
    if region == 3:
        return (0, q, val)
    if region == 4:
        return (t, 0, val)
    return (val, 0, q)


def scale_rgb(rgb, bright_pct):
    return (
        (rgb[0] * bright_pct) // 100,
        (rgb[1] * bright_pct) // 100,
        (rgb[2] * bright_pct) // 100,
    )


class TreeState:
    def __init__(self):
        self.pattern_id = 12
        self.palette_id = 0
        self.red = 255
        self.green = 120
        self.blue = 30
        self.brightness = 70
        self.speed = 50
        self.tree_type = TREE_TYPE_PCB
        self.melody_id = 0
        self.playback_state = 0
        self.volume = 60
        self.tempo = 100
        self.error_code = 0
        self.presets = [dict(p) for p in DEFAULT_PRESETS]
        self.next_preset_num = 1
        self.boot_time = time.monotonic()

    def load(self):
        try:
            with open(STATE_FILE, "r") as f:
                d = json.load(f)
            self.pattern_id = max(0, min(12, int(d.get("pattern_id", self.pattern_id))))
            self.palette_id = max(0, min(9, int(d.get("palette_id", self.palette_id))))
            self.red = max(0, min(255, int(d.get("red", self.red))))
            self.green = max(0, min(255, int(d.get("green", self.green))))
            self.blue = max(0, min(255, int(d.get("blue", self.blue))))
            self.brightness = max(0, min(100, int(d.get("brightness", self.brightness))))
            self.speed = max(1, min(100, int(d.get("speed", self.speed))))
            if "tree_type" in d:
                raw_tt = d["tree_type"]
                if isinstance(raw_tt, int):
                    self.tree_type = TREE_TYPE_HOLZ if raw_tt == 1 else TREE_TYPE_PCB
                else:
                    self.tree_type = normalize_tree_type(raw_tt)
            self.melody_id = max(0, min(4, int(d.get("melody_id", self.melody_id))))
            self.volume = max(0, min(100, int(d.get("volume", self.volume))))
            self.tempo = max(50, min(200, int(d.get("tempo", self.tempo))))
        except OSError:
            pass
        except ValueError:
            pass

        try:
            with open(PRESETS_FILE, "r") as f:
                loaded = json.load(f)
            if isinstance(loaded, list) and loaded:
                self.presets = loaded[:16]
        except OSError:
            pass
        except ValueError:
            pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({
                    "pattern_id": self.pattern_id,
                    "palette_id": self.palette_id,
                    "red": self.red,
                    "green": self.green,
                    "blue": self.blue,
                    "brightness": self.brightness,
                    "speed": self.speed,
                    "tree_type": self.tree_type,
                    "melody_id": self.melody_id,
                    "volume": self.volume,
                    "tempo": self.tempo,
                }, f)
        except OSError:
            pass

    def save_presets(self):
        try:
            with open(PRESETS_FILE, "w") as f:
                json.dump(self.presets, f)
        except OSError:
            pass

    def status_dict(self, ap_ip, sta_count):
        return {
            "uptime": int(time.monotonic() - self.boot_time),
            "pattern_id": self.pattern_id,
            "palette_id": self.palette_id,
            "red": self.red,
            "green": self.green,
            "blue": self.blue,
            "brightness": self.brightness,
            "speed": self.speed,
            "tree_type": self.tree_type,
            "melody_id": self.melody_id,
            "playback_state": self.playback_state,
            "volume": self.volume,
            "tempo": self.tempo,
            "sta_count": sta_count,
            "error_code": self.error_code,
            "ssid": AP_SSID,
            "ip": ap_ip,
            "firmware": FIRMWARE_VERSION,
        }


# --- Geometry Pre-calculation ---
DIST_LUT = tuple(build_distance_lut(ep) for ep in EPICENTERS)
CX, CY = CENTER_TREE
GEOM = tuple(
    (x, y, (x - CX) * 0.08, (y - CY) * 0.08, r, theta, seg)
    for (x, y, seg), (r, theta) in zip(PIXEL_COORDS, POLAR_TREE)
)
VSEG_MAP = [0] * NUM_PIXELS
for _vidx, _indices in enumerate(VIRTUAL_SEGMENTS):
    for _li in _indices:
        VSEG_MAP[_li] = _vidx


def render_frame(pixels, state, frame_idx):
    pat = state.pattern_id
    bright = state.brightness
    spd = state.speed
    pal_id = state.palette_id

    if pat == 0:  # Off
        pixels.fill((0, 0, 0))
    elif pat == 1:  # Static
        pixels.fill(scale_rgb((state.red, state.green, state.blue), bright))
    elif pat == 2:  # Rainbow Wave
        val = (255 * bright) // 100
        shift = (frame_idx * spd) // 5
        for i in range(NUM_PIXELS):
            hue = ((i * 256 // NUM_PIXELS) + shift) & 0xFF
            pixels[i] = hsv_to_rgb(hue, val)
    elif pat == 3:  # Sparkle
        dim = ((state.red * bright) // 300, (state.green * bright) // 300, (state.blue * bright) // 300)
        hi = scale_rgb((state.red, state.green, state.blue), bright)
        step = frame_idx * spd * 1103515245
        for i in range(NUM_PIXELS):
            h = (i * 2654435761 + step) & 0xFFFFFF
            pixels[i] = hi if (h % 100) < 15 else dim
    elif pat == 4:  # Festive Candle
        br, bg, bb = scale_rgb((state.red, state.green, state.blue), bright)
        b_dim = bb >> 2
        for i in range(NUM_PIXELS):
            flicker = (i * 17 + frame_idx * spd * 7) % 50
            pixels[i] = (br, (bg * (50 + flicker)) // 100, b_dim)
    elif pat == 5:  # Twinkle
        br, bg, bb = scale_rgb((state.red, state.green, state.blue), bright)
        step = (frame_idx * spd) >> 1
        for i in range(NUM_PIXELS):
            phase = (i * 37 + step) & 0xFF
            factor = (phase * 2) if phase < 128 else ((255 - phase) * 2)
            pixels[i] = ((br * factor) // 255, (bg * factor) // 255, (bb * factor) // 255)
    elif pat == 6:  # Lauflicht (Comet Chase)
        if state.red == 0 and state.green == 0 and state.blue == 0:
            hr, hg, hb = 0, 220, 255
        else:
            hr, hg, hb = state.red, state.green, state.blue
        head = ((frame_idx * spd) // 10) % NUM_PIXELS
        for i in range(NUM_PIXELS):
            dist = (head - i) if head >= i else (NUM_PIXELS - i + head)
            if dist < 8:
                pixels[i] = scale_rgb((hr >> dist, hg >> dist, hb >> dist), bright)
            else:
                pixels[i] = (0, 0, 0)
    elif pat == 7:  # Segments
        active_vseg = (pal_id - 1) if 1 <= pal_id <= 6 else (((frame_idx * spd) // 300) % 6)
        col = scale_rgb(SEG_COLORS[active_vseg], bright)
        for i in range(NUM_PIXELS):
            pixels[i] = col if VSEG_MAP[i] == active_vseg else (0, 0, 0)
    elif pat == 8:  # Radial Shockwave
        lut = DIST_LUT[pal_id % len(DIST_LUT)]
        radius = (frame_idx * (0.4 + spd * 0.03)) % 95.0
        wave_w = 9.0
        for i in range(NUM_PIXELS):
            d = abs(lut[i] - radius)
            if d < wave_w:
                inten = 1.0 - (d / wave_w)
                sq = inten * inten
                base = SEG_COLORS[PIXEL_COORDS[i][2] % 5]
                wb = int(180.0 * sq * sq)
                r = min(255, int(base[0] * sq) + wb)
                g = min(255, int(base[1] * sq) + wb)
                b = min(255, int(base[2] * sq) + wb)
                pixels[i] = scale_rgb((r, g, b), bright)
            else:
                pixels[i] = (0, 0, 0)
    elif pat == 9:  # 2D Interference Plasma
        t = frame_idx * (0.01 + spd * 0.0012)
        val = (255 * bright) // 100
        for i in range(NUM_PIXELS):
            _, _, nx, ny, r, _, seg = GEOM[i]
            v1 = math.sin(nx + t * 2.1)
            v2 = math.sin(ny + t * 1.7)
            v3 = math.sin((nx + ny + r * 0.12) - t * 2.5)
            hue_f = ((v1 + v2 + v3) * 0.16 + seg * 0.04 + 4.0) % 1.0
            pixels[i] = hsv_to_rgb(int(hue_f * 255.0) & 0xFF, val)
    elif pat == 10:  # Polar Vortex
        t = frame_idx * (0.01 + spd * 0.0012)
        angle_sweep = t * 3.5
        max_v = (255.0 * bright) / 100.0
        for i in range(NUM_PIXELS):
            _, _, _, _, r, theta, _ = GEOM[i]
            wave = (math.sin(theta * 2.0 - angle_sweep + r * 0.15) + 1.0) * 0.5
            hue_f = ((theta / (2.0 * math.pi)) + t * 0.1 + 2.0) % 1.0
            pixels[i] = hsv_to_rgb(int(hue_f * 255.0) & 0xFF, int(max_v * wave))
    elif pat == 11:  # Gravity Pulse
        t = frame_idx * (0.01 + spd * 0.0012)
        y_front = 68.551 - ((t * 48.0) % 80.0)
        max_v = (255.0 * bright) / 100.0
        for i in range(NUM_PIXELS):
            _, y, _, _, _, _, seg = GEOM[i]
            dy = y - y_front
            if 0.0 <= dy < 22.0:
                val_f = 1.0 - (dy / 22.0)
                hue_f = (seg * 0.08 + dy * 0.01) % 1.0
                pixels[i] = hsv_to_rgb(int(hue_f * 255.0) & 0xFF, int(max_v * val_f))
            else:
                pixels[i] = (0, 0, 0)
    else:  # 12: TwinkleFOX
        pal = PALETTES[pal_id % len(PALETTES)]
        tf_speed = max(2, (spd * 8) // 100)
        ms = frame_idx * 20
        render_twinkle_tree(pixels, ms, pal, PAL_FAIRY_LIGHT, speed=tf_speed, density=5)
        if bright < 100:
            for i in range(NUM_PIXELS):
                pixels[i] = scale_rgb(pixels[i], bright)

    if getattr(state, "tree_type", TREE_TYPE_PCB) == TREE_TYPE_HOLZ and not (isinstance(pixels, MappedPixels) and pixels._fixed_tree_type is None):
        s, e = SEGMENTS[SEG_BOUGH_MID]
        for k in range((e - s) // 2):
            a, b = s + k, e - 1 - k
            pixels[a], pixels[b] = pixels[b], pixels[a]

    pixels.show()


# --- RTTTL Non-blocking Audio Player ---
def parse_rtttl_notes(rtttl):
    parts = rtttl.split(":")
    if len(parts) < 3:
        return []
    dd, doct, bpm = 4, 5, 120
    for tok in parts[1].split(","):
        tok = tok.strip()
        if tok.startswith("d="):
            dd = int(tok[2:]) or 4
        elif tok.startswith("o="):
            doct = int(tok[2:]) or 5
        elif tok.startswith("b="):
            bpm = int(tok[2:]) or 120

    whole_ms = (60000.0 * 4.0) / bpm
    notes = []
    for raw in parts[2].split(","):
        s = raw.strip().lower()
        if not s:
            continue
        idx = 0
        dur_str = ""
        while idx < len(s) and s[idx].isdigit():
            dur_str += s[idx]
            idx += 1
        dur = int(dur_str) if dur_str else dd
        dotted = False
        if idx < len(s) and s[idx] == ".":
            dotted = True
            idx += 1
        if idx >= len(s):
            continue
        note_ch = s[idx]
        idx += 1
        if idx < len(s) and s[idx] == "#":
            note_ch += "#"
            idx += 1
        if idx < len(s) and s[idx] == ".":
            dotted = True
            idx += 1
        oct_val = doct
        if idx < len(s) and s[idx].isdigit():
            oct_val = int(s[idx])
            idx += 1
        if idx < len(s) and s[idx] == ".":
            dotted = True

        note_ms = whole_ms / dur
        if dotted:
            note_ms *= 1.5

        if note_ch in ("p", "r"):
            freq = 0
        else:
            base = BASE_FREQS.get(note_ch, 0)
            if base == 0 or oct_val < 1 or oct_val > 8:
                freq = 0
            elif oct_val == 4:
                freq = base
            elif oct_val > 4:
                freq = base << (oct_val - 4)
            else:
                freq = base >> (4 - oct_val)
        notes.append((freq, note_ms))
    return notes


PARSED_MELODIES = tuple(parse_rtttl_notes(s) if s else [] for s in RTTTL_SCORES)


class AudioPlayer:
    def __init__(self, pwm):
        self.pwm = pwm
        self.active_melody = 0
        self.note_idx = 0
        self.next_step_at = 0.0
        self.oneshot_until = 0.0

    def _set_tone(self, freq_hz, volume):
        if freq_hz <= 0 or volume <= 0:
            self.pwm.duty_cycle = 0
            return
        self.pwm.frequency = int(freq_hz)
        self.pwm.duty_cycle = (32768 * max(0, min(100, volume))) // 100

    def play_oneshot(self, freq_hz, duration_ms, volume):
        if freq_hz < 50 or freq_hz > 8000 or duration_ms <= 0 or duration_ms > 5000:
            return False
        self._set_tone(freq_hz, volume)
        self.oneshot_until = time.monotonic() + (duration_ms / 1000.0)
        return True

    def update(self, state, now):
        if self.oneshot_until > 0.0:
            if now < self.oneshot_until:
                return
            self.oneshot_until = 0.0
            self.pwm.duty_cycle = 0

        if state.playback_state == 0 or state.melody_id == 0:
            self.pwm.duty_cycle = 0
            self.active_melody = 0
            self.note_idx = 0
            return

        if state.playback_state == 2:  # Pause
            self.pwm.duty_cycle = 0
            return

        notes = PARSED_MELODIES[state.melody_id]
        if not notes:
            self.pwm.duty_cycle = 0
            return

        if self.active_melody != state.melody_id:
            self.active_melody = state.melody_id
            self.note_idx = 0
            self.next_step_at = 0.0

        if now >= self.next_step_at:
            freq, base_ms = notes[self.note_idx % len(notes)]
            self.note_idx = (self.note_idx + 1) % len(notes)
            dur_s = (base_ms * (100.0 / max(50, min(200, state.tempo)))) / 1000.0
            self._set_tone(freq, state.volume)
            self.next_step_at = now + max(0.02, dur_s)


# --- Captive Portal DNS Builder ---
def build_dns_response(query, ap_ip_bytes):
    qlen = len(query)
    if qlen < 17 or qlen > 512:
        return b""
    pos = 12
    while pos < qlen:
        lbl = query[pos]
        if lbl == 0:
            pos += 1
            break
        if (lbl & 0xC0) != 0 or pos + 1 + lbl >= qlen:
            return b""
        pos += 1 + lbl
    if pos + 4 > qlen:
        return b""

    qtype = (query[pos] << 8) | query[pos + 1]
    qclass = (query[pos + 2] << 8) | query[pos + 3]
    q_end = pos + 4
    is_a = (qtype == 1 and qclass == 1)

    hdr = bytearray(query[:q_end])
    hdr[2] = 0x84 | (query[2] & 0x01)
    hdr[3] = 0x80
    hdr[4], hdr[5] = 0x00, 0x01
    hdr[6], hdr[7] = 0x00, (0x01 if is_a else 0x00)
    hdr[8:12] = b"\x00\x00\x00\x00"
    if not is_a:
        return bytes(hdr)

    ans = b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04" + bytes(ap_ip_bytes)
    return bytes(hdr) + ans


# --- HTTP Captive Portal & REST Handlers ---
def handle_http_request(raw_req, state, audio, ap_ip, sta_count, web_ui_gz):
    head_end = raw_req.find(b"\r\n\r\n")
    if head_end < 0:
        return b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"

    header_lines = raw_req[:head_end].decode("utf-8", "ignore").split("\r\n")
    req_parts = header_lines[0].split(" ")
    if len(req_parts) < 2:
        return b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"

    method = req_parts[0].upper()
    uri = req_parts[1].split("?")[0]
    host = ""
    for line in header_lines[1:]:
        if line.lower().startswith("host:"):
            host = line.split(":", 1)[1].strip()
            break

    body = raw_req[head_end + 4 :]

    def redirect_302():
        return (
            "HTTP/1.1 302 Found\r\n"
            f"Location: http://{ap_ip}/\r\n"
            "Cache-Control: no-store, no-cache, must-revalidate\r\n"
            "Content-Length: 0\r\n"
            "Connection: close\r\n\r\n"
        ).encode("utf-8")

    def json_resp(obj, code=200):
        payload = json.dumps(obj).encode("utf-8")
        status = "200 OK" if code == 200 else "400 Bad Request"
        return (
            f"HTTP/1.1 {status}\r\n"
            "Content-Type: application/json\r\n"
            "Cache-Control: no-store\r\n"
            f"Content-Length: {len(payload)}\r\n"
            "Connection: close\r\n\r\n"
        ).encode("utf-8") + payload

    if method == "GET" and uri in PROBE_URIS:
        return redirect_302()

    if method == "GET" and uri == "/":
        host_base = host.split(":")[0]
        if host_base and host_base not in (ap_ip, "xmastree.local"):
            return redirect_302()
        hdr = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "Content-Encoding: gzip\r\n"
            "Cache-Control: no-store\r\n"
            f"Content-Length: {len(web_ui_gz)}\r\n"
            "Connection: close\r\n\r\n"
        ).encode("utf-8")
        return hdr + web_ui_gz

    if method == "GET" and uri == "/api/status":
        return json_resp(state.status_dict(ap_ip, sta_count))

    if method == "POST" and uri == "/api/lighting":
        try:
            d = json.loads(body.decode("utf-8"))
        except Exception:
            return json_resp({"error": "invalid json"}, 400)
        if "pattern_id" in d:
            v = int(d["pattern_id"])
            if not (0 <= v <= 12):
                return json_resp({"error": "invalid pattern_id"}, 400)
            state.pattern_id = v
        if "palette_id" in d:
            v = int(d["palette_id"])
            if not (0 <= v <= 9):
                return json_resp({"error": "invalid palette_id"}, 400)
            state.palette_id = v
        if "red" in d:
            state.red = max(0, min(255, int(d["red"])))
        if "green" in d:
            state.green = max(0, min(255, int(d["green"])))
        if "blue" in d:
            state.blue = max(0, min(255, int(d["blue"])))
        if "brightness" in d:
            state.brightness = max(0, min(100, int(d["brightness"])))
        if "speed" in d:
            state.speed = max(1, min(100, int(d["speed"])))
        if "tree_type" in d:
            raw_tt = d["tree_type"]
            if isinstance(raw_tt, int) and raw_tt in (0, 1):
                state.tree_type = TREE_TYPE_HOLZ if raw_tt == 1 else TREE_TYPE_PCB
            else:
                try:
                    state.tree_type = normalize_tree_type(raw_tt)
                except ValueError:
                    return json_resp({"error": "invalid tree_type"}, 400)
        state.save_state()
        return json_resp(state.status_dict(ap_ip, sta_count))

    if method == "POST" and uri == "/api/audio":
        try:
            d = json.loads(body.decode("utf-8"))
        except Exception:
            return json_resp({"error": "invalid json"}, 400)
        if "freq_hz" in d and int(d["freq_hz"]) > 0:
            freq = int(d["freq_hz"])
            dur = int(d.get("duration_ms", 250))
            vol = int(d.get("volume", state.volume))
            if not audio.play_oneshot(freq, dur, vol):
                return json_resp({"error": "invalid tone"}, 400)
            return json_resp(state.status_dict(ap_ip, sta_count))
        if "melody_id" in d:
            v = int(d["melody_id"])
            if not (0 <= v <= 4):
                return json_resp({"error": "invalid melody_id"}, 400)
            state.melody_id = v
        if "playback_state" in d:
            v = int(d["playback_state"])
            if not (0 <= v <= 2):
                return json_resp({"error": "invalid playback_state"}, 400)
            state.playback_state = v
        if "volume" in d:
            state.volume = max(0, min(100, int(d["volume"])))
        if "tempo" in d:
            t = int(d["tempo"])
            if not (50 <= t <= 200):
                return json_resp({"error": "invalid tempo"}, 400)
            state.tempo = t
        state.save_state()
        return json_resp(state.status_dict(ap_ip, sta_count))

    if method == "GET" and uri == "/api/presets":
        return json_resp(state.presets)

    if method == "POST" and uri == "/api/presets":
        try:
            d = json.loads(body.decode("utf-8"))
        except Exception:
            return json_resp({"error": "invalid json"}, 400)
        name = str(d.get("name", "")).strip()[:32]
        if not name or len(state.presets) >= 16:
            return json_resp({"error": "invalid preset"}, 400)
        pid = str(d.get("id", "")).strip() or f"user-{state.next_preset_num}"
        state.next_preset_num += 1
        item = {
            "id": pid,
            "name": name,
            "pattern_id": max(0, min(12, int(d.get("pattern_id", state.pattern_id)))),
            "palette_id": max(0, min(9, int(d.get("palette_id", state.palette_id)))),
            "red": max(0, min(255, int(d.get("red", state.red)))),
            "green": max(0, min(255, int(d.get("green", state.green)))),
            "blue": max(0, min(255, int(d.get("blue", state.blue)))),
            "brightness": max(0, min(100, int(d.get("brightness", state.brightness)))),
            "speed": max(1, min(100, int(d.get("speed", state.speed)))),
            "melody_id": max(0, min(4, int(d.get("melody_id", state.melody_id)))),
            "volume": max(0, min(100, int(d.get("volume", state.volume)))),
            "tempo": max(50, min(200, int(d.get("tempo", state.tempo)))),
        }
        state.presets = [p for p in state.presets if p["id"] != pid] + [item]
        state.save_presets()
        return json_resp(state.presets)

    if method == "POST" and uri == "/api/presets/apply":
        try:
            d = json.loads(body.decode("utf-8"))
        except Exception:
            return json_resp({"error": "invalid json"}, 400)
        pid = str(d.get("id", ""))
        match = next((p for p in state.presets if p["id"] == pid), None)
        if not match:
            return json_resp({"error": "not found"}, 400)
        state.pattern_id = match["pattern_id"]
        state.palette_id = match["palette_id"]
        state.red = match["red"]
        state.green = match["green"]
        state.blue = match["blue"]
        state.brightness = match["brightness"]
        state.speed = match["speed"]
        state.melody_id = match["melody_id"]
        state.volume = match["volume"]
        state.tempo = match["tempo"]
        state.playback_state = 0 if state.melody_id == 0 else 1
        state.save_state()
        return json_resp(state.status_dict(ap_ip, sta_count))

    if method == "POST" and uri == "/api/presets/delete":
        try:
            d = json.loads(body.decode("utf-8"))
        except Exception:
            return json_resp({"error": "invalid json"}, 400)
        pid = str(d.get("id", ""))
        before = len(state.presets)
        state.presets = [p for p in state.presets if p["id"] != pid]
        if len(state.presets) == before:
            return json_resp({"error": "not found"}, 400)
        state.save_presets()
        return json_resp(state.presets)

    return redirect_302()


def send_all(conn, data):
    view = memoryview(data)
    sent = 0
    total = len(data)
    deadline = time.monotonic() + 1.5
    while sent < total and time.monotonic() < deadline:
        try:
            n = conn.send(view[sent:])
            if n <= 0:
                break
            sent += n
        except OSError as e:
            if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                time.sleep(0.002)
                continue
            break


def main():
    state = TreeState()
    state.load()

    # Helligkeit wird in render_frame() wahrnehmungsgleich angewendet; MappedPixels korrigiert
    # beim show() genau einmal per Gamma-Tabelle (GAMMA_LUT in tannenbaum_layout.py). Holz-Swap macht render_frame().
    pixels = MappedPixels(
        neopixel.NeoPixel(
            PIN_NEOPIXEL, NUM_PIXELS, brightness=1.0, auto_write=False, pixel_order=neopixel.GRB
        ),
        tree_type=TREE_TYPE_PCB,
        gamma=True,
    )
    pwm = pwmio.PWMOut(board.D0, duty_cycle=0, frequency=440, variable_frequency=True)
    audio = AudioPlayer(pwm)

    with open(WEB_UI_GZ_FILE, "rb") as f:
        web_ui_gz = f.read()

    wifi.radio.start_ap(ssid=AP_SSID)
    ap_ip_obj = wifi.radio.ipv4_address_ap
    ap_ip = str(ap_ip_obj)
    ap_ip_bytes = bytes(ap_ip_obj)
    print(f"AITY Xmas Tree Captive Portal active: SSID={AP_SSID} IP={ap_ip}")

    pool = socketpool.SocketPool(wifi.radio)

    dns_sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)
    dns_sock.setblocking(False)
    dns_sock.bind(("0.0.0.0", 53))

    http_sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
    http_sock.setblocking(False)
    http_sock.bind(("0.0.0.0", 80))
    http_sock.listen(4)

    dns_buf = bytearray(512)
    http_buf = bytearray(2048)
    frame_idx = 0
    next_frame_at = time.monotonic()

    while True:
        now = time.monotonic()

        # 1. Service non-blocking DNS captive portal queries
        for _ in range(4):
            try:
                nbytes, addr = dns_sock.recvfrom_into(dns_buf)
                if nbytes > 0:
                    resp = build_dns_response(bytes(dns_buf[:nbytes]), ap_ip_bytes)
                    if resp:
                        dns_sock.sendto(resp, addr)
            except OSError:
                break

        # 2. Service non-blocking HTTP requests
        for _ in range(4):
            try:
                conn, _ = http_sock.accept()
            except OSError:
                break
            try:
                conn.settimeout(0.25)
                nbytes = conn.recv_into(http_buf)
                if nbytes > 0:
                    sta_count = len(getattr(wifi.radio, "stations_ap", ()) or ())
                    resp = handle_http_request(
                        bytes(http_buf[:nbytes]), state, audio, ap_ip, sta_count, web_ui_gz
                    )
                    send_all(conn, resp)
            except OSError:
                pass
            finally:
                try:
                    conn.close()
                except OSError:
                    pass

        # 3. Step RTTTL audio player
        audio.update(state, now)

        # 4. Render 50 FPS NeoPixel frame
        if now >= next_frame_at:
            render_frame(pixels, state, frame_idx)
            frame_idx += 1
            next_frame_at = now + 0.02

        time.sleep(0.002)


if __name__ == "__main__":
    main()
