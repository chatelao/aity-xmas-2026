# code.99-unified.py
# Unified Firmware: Alle Tannenbaum-Animationen in einem Skript
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6
# Abhaengigkeiten: /lib/neopixel.mpy, /lib/tannenbaum_layout.py, /lib/tannenbaum_palettes.py
#
# Steuerung ueber D5 (Zurueck / Langsamer) & D6 (Vor / Schneller):
# - Einzelklick (Single Tap): Sujet/Modus wechseln (D5: vorheriges, D6: naechstes)
# - Langer Klick (Long Hold): Farbpalette wechseln (D5: vorherige, D6: naechste)
# - Doppelklick (Double Tap): Geschwindigkeit anpassen (D5: langsamer, D6: schneller)
# - Jede Aenderung (Modus/Palette/Tempo, per Taster oder seriell) wird automatisch gespeichert
#   (microcontroller.nvm) und nach einem Stromunterbruch wiederhergestellt
#
# Serielle Konsole (USB, Terminal anklicken & tippen):
# - '+' / '-'        : naechster / vorheriger Modus
# - Pfeil hoch/runter: schneller / langsamer
# - Pfeil rechts/links: naechste / vorherige Palette

import time
import math
import sys
try:
    import supervisor
except ImportError:
    supervisor = None
try:
    import microcontroller
    NVM = microcontroller.nvm
except (ImportError, AttributeError, NotImplementedError):
    NVM = None
from tannenbaum_layout import (
    NUM_PIXELS, init_pixels, init_buttons,
    PIXEL_COORDS, NORM_COORDS, CENTER_TREE, CENTER_STAR, POLAR_TREE,
    Y_MIN, Y_MAX, WIDTH_MM, HEIGHT_MM,
    SEG_BOUGH_LOW, SEG_BOUGH_MID, SEG_BOUGH_HIGH, SEG_STEM, SEG_STAR, SEGMENTS,
    VSEG_STAR_INNER, VSEG_STAR_OUTER, VIRTUAL_SEGMENTS,
    EPICENTERS, GAMMA_LUT, build_distance_lut,
)
from tannenbaum_palettes import (
    BLACK, PALETTES, PALETTE_NAMES, PAL_FAIRY_LIGHT,
    color_from_palette, blend_palette_toward, render_twinkle_tree,
)

# --- Hardware-Setup ---
TREE_TYPE = "PCB"  # "PCB" (Standard) oder "Holz" (zweitlaengstes Segment rueckwaerts)
pixels = init_pixels(brightness=0.35, tree_type=TREE_TYPE)
btn_d5, btn_d6 = init_buttons()

# --- Geometrie-Vorberechnung ---
DIST_LUT = tuple(build_distance_lut(ep) for ep in EPICENTERS)
CX, CY = CENTER_TREE
STAR_CX, STAR_CY = CENTER_STAR
GEOM = tuple(
    (x, y, (x - CX) * 0.08, (y - CY) * 0.08, r, theta, seg)
    for (x, y, seg), (r, theta) in zip(PIXEL_COORDS, POLAR_TREE)
)

# --- Modi & Geschwindigkeitsstufen ---
MODE_NAMES = (
    "0: TwinkleFOX",
    "1: Sechs LEDs",
    "2: Lauflicht",
    "3: Segmente",
    "4: Koordinaten-Welle",
    "5: 2D-Plasma",
    "6: Polar-Wirbel",
    "7: Gravitations-Puls",
    "8: Adventskranz",
    "9: Schlittenfahrt",
    "10: Stern von Bethlehem",
    "11: Kaminfeuer & Eis",
    "12: Stille Nacht Atemzug",
)
NUM_MODES = len(MODE_NAMES)

SPEED_FACTORS = (0.25, 0.35, 0.5, 0.7, 1.0, 1.4, 2.0, 2.8, 4.0)
DEFAULT_SPEED_IDX = 4  # 1.0x

# --- Gesten-Erkennung (Single Tap, Double Tap, Long Hold) ---
DEBOUNCE_S = 0.025
DOUBLE_TAP_S = 0.35
LONG_HOLD_S = 0.55
HOLD_REPEAT_S = 0.25


class ButtonGesture:
    def __init__(self, pin):
        self.pin = pin
        self.raw_pressed = False
        self.debounced_pressed = False
        self.last_raw_change = 0.0
        self.press_time = 0.0
        self.release_time = 0.0
        self.pending_tap = False
        self.long_active = False
        self.last_repeat = 0.0
        self.suppress_release = False

    def update(self, now):
        events = []
        raw = not self.pin.value
        if raw != self.raw_pressed:
            self.raw_pressed = raw
            self.last_raw_change = now

        if (now - self.last_raw_change) >= DEBOUNCE_S and raw != self.debounced_pressed:
            self.debounced_pressed = raw
            if raw:
                # Gedrueckt
                self.press_time = now
                self.long_active = False
                if self.pending_tap and (now - self.release_time) <= DOUBLE_TAP_S:
                    self.pending_tap = False
                    self.suppress_release = True
                    events.append("double_tap")
                else:
                    self.suppress_release = False
            else:
                # Losgelassen
                if not self.suppress_release and not self.long_active:
                    self.pending_tap = True
                    self.release_time = now
                self.long_active = False
                self.suppress_release = False

        if self.debounced_pressed and not self.suppress_release:
            if not self.long_active and (now - self.press_time) >= LONG_HOLD_S:
                self.long_active = True
                self.pending_tap = False
                self.last_repeat = now
                events.append("long_hold")
            elif self.long_active and (now - self.last_repeat) >= HOLD_REPEAT_S:
                self.last_repeat = now
                events.append("long_hold")

        if self.pending_tap and (now - self.release_time) > DOUBLE_TAP_S:
            self.pending_tap = False
            events.append("single_tap")

        return events


gest_d5 = ButtonGesture(btn_d5)
gest_d6 = ButtonGesture(btn_d6)

# --- Persistenz (nvm: Magic 'XM' + Modus, Palette, Tempo, Pruefsumme) ---
SAVE_MAGIC = b"XM"
SAVE_DELAY_S = 0.8  # Entprellung: schont den Flash bei schnellen Folgeaenderungen


def save_selection(mode, pal, speed):
    if NVM is None:
        print("Speichern nicht moeglich (kein nvm)")
        return False
    try:
        data = bytes((mode, pal, speed))
        blob = SAVE_MAGIC + data + bytes(((mode + pal + speed) & 0xFF,))
        if bytes(NVM[0:6]) == blob:
            return True
        NVM[0:6] = blob
        print(f"Gespeichert: Modus {mode} | Palette {pal} | Tempo-Stufe {speed}")
        return True
    except Exception as e:
        print("Speichern fehlgeschlagen:", e)
        return False


def load_selection():
    if NVM is None:
        return None
    try:
        raw = bytes(NVM[0:6])
    except Exception:
        return None
    if raw[0:2] != SAVE_MAGIC:
        return None
    mode, pal, speed, chk = raw[2], raw[3], raw[4], raw[5]
    if chk != ((mode + pal + speed) & 0xFF):
        return None
    if mode >= NUM_MODES or pal >= len(PALETTES) or speed >= len(SPEED_FACTORS):
        return None
    return mode, pal, speed


# --- Zustand ---
class _State:
    def __init__(self):
        self.mode_idx = 0
        self.pal_idx = 0
        self.speed_idx = DEFAULT_SPEED_IDX
        self.save_due = None
        self.esc_buf = ""
        self.chase_accum = 0.0
        self.seg_accum = 0.0
        self.wave_radius = 0.0


st = _State()
_saved = load_selection()
if _saved is not None:
    st.mode_idx, st.pal_idx, st.speed_idx = _saved
    print("Gespeicherte Auswahl wiederhergestellt")

current_palette = PALETTES[st.pal_idx]
st.target_palette = PALETTES[st.pal_idx]

# Animations-Zustand
last_now = time.monotonic()
phase_t = 0.0
chase_head = 0
seg_active = 0
wave_epi = 0


def reset_mode_state():
    pixels.fill(BLACK)
    st.chase_accum = 0.0
    st.seg_accum = 0.0
    st.wave_radius = 0.0


def change_mode(step):
    st.save_due = time.monotonic() + SAVE_DELAY_S
    st.mode_idx = (st.mode_idx + step) % NUM_MODES
    reset_mode_state()
    print(f"Modus: {MODE_NAMES[st.mode_idx]}")


def change_palette(step):
    st.save_due = time.monotonic() + SAVE_DELAY_S
    st.pal_idx = (st.pal_idx + step) % len(PALETTES)
    st.target_palette = PALETTES[st.pal_idx]
    print(f"Palette: {PALETTE_NAMES[st.pal_idx]}")


def change_speed(step):
    n = st.speed_idx + step
    if 0 <= n < len(SPEED_FACTORS):
        st.speed_idx = n
        st.save_due = time.monotonic() + SAVE_DELAY_S
        print(f"Tempo: {SPEED_FACTORS[st.speed_idx]}x (Stufe {st.speed_idx}/8)")


def handle_serial_key(ch):
    # Pfeiltasten kommen als ESC [ A/B/C/D
    if st.esc_buf:
        st.esc_buf += ch
        if len(st.esc_buf) == 2:
            if ch != "[":
                st.esc_buf = ""
            return
        st.esc_buf = ""
        if ch == "A":
            change_speed(1)
        elif ch == "B":
            change_speed(-1)
        elif ch == "C":
            change_palette(1)
        elif ch == "D":
            change_palette(-1)
        return
    if ch == "\x1b":
        st.esc_buf = ch
    elif ch in "+=":
        change_mode(1)
    elif ch in "-_":
        change_mode(-1)


def poll_serial():
    if supervisor is None:
        return
    n = 0
    while supervisor.runtime.serial_bytes_available and n < 8:
        handle_serial_key(sys.stdin.read(1))
        n += 1


print("=== AITY XMAS 2026 UNIFIED FIRMWARE ===")
print("Single Tap D5/D6: Sujet | Long Hold D5/D6: Palette | Double Tap D5/D6: Tempo")
print(f"Modus: {MODE_NAMES[st.mode_idx]} | Palette: {PALETTE_NAMES[st.pal_idx]} | Tempo: {SPEED_FACTORS[st.speed_idx]}x")

while True:
    now = time.monotonic()
    dt = now - last_now
    if dt < 0.0:
        dt = 0.0
    elif dt > 0.2:
        dt = 0.2
    last_now = now

    # --- Serielle Steuerung ---
    poll_serial()

    # --- Taster-Gesten auswerten ---
    ev5 = gest_d5.update(now)
    ev6 = gest_d6.update(now)

    for ev in ev5:
        if ev == "single_tap":
            change_mode(-1)
        elif ev == "long_hold":
            change_palette(-1)
        elif ev == "double_tap":
            change_speed(-1)

    for ev in ev6:
        if ev == "single_tap":
            change_mode(1)
        elif ev == "long_hold":
            change_palette(1)
        elif ev == "double_tap":
            change_speed(1)

    # Automatisch speichern (entprellt)
    if st.save_due is not None and now >= st.save_due:
        st.save_due = None
        save_selection(st.mode_idx, st.pal_idx, st.speed_idx)

    # Sanfter Paletten-Uebergang
    if current_palette != st.target_palette:
        current_palette = blend_palette_toward(current_palette, st.target_palette, 18)

    speed_factor = SPEED_FACTORS[st.speed_idx]
    phase_t += dt * speed_factor

    # --- Aktiven Modus rendern ---
    if st.mode_idx == 0:
        # 0: TwinkleFOX
        render_twinkle_tree(
            pixels,
            int(now * 1000),
            current_palette,
            star_palette=PAL_FAIRY_LIGHT,
            speed=st.speed_idx,
            density=5,
        )

    elif st.mode_idx == 1:
        # 1: Sechs LEDs (statisch aus aktiver Palette)
        pixels.fill(BLACK)
        for i in range(6):
            pixels[i] = color_from_palette(current_palette, i * 42)

    elif st.mode_idx == 2:
        # 2: Lauflicht mit Schweif
        st.chase_accum += dt * speed_factor
        if st.chase_accum >= 0.04:
            st.chase_accum = 0.0
            for i in range(NUM_PIXELS):
                r, g, b = pixels[i]
                pixels[i] = (r >> 1, g >> 1, b >> 1)
            pixels[chase_head] = color_from_palette(current_palette, (chase_head * 4) & 0xFF)
            chase_head = (chase_head + 1) % NUM_PIXELS

    elif st.mode_idx == 3:
        # 3: Segmente durchlaufen
        st.seg_accum += dt * speed_factor
        if st.seg_accum >= 0.6:
            st.seg_accum = 0.0
            seg_active = (seg_active + 1) % len(VIRTUAL_SEGMENTS)
        pixels.fill(BLACK)
        col = color_from_palette(current_palette, (seg_active * 42) & 0xFF)
        for i in VIRTUAL_SEGMENTS[seg_active]:
            pixels[i] = col

    elif st.mode_idx == 4:
        # 4: Koordinaten-Wellenexplosion
        st.wave_radius += dt * 45.0 * speed_factor
        if st.wave_radius > 95.0:
            st.wave_radius = 0.0
            wave_epi = (wave_epi + 1) % len(EPICENTERS)
        dists = DIST_LUT[wave_epi]
        wave_width = 9.0
        for i in range(NUM_PIXELS):
            d = abs(dists[i] - st.wave_radius)
            if d < wave_width:
                intensity = 1.0 - (d / wave_width)
                intensity_sq = intensity * intensity
                seg = PIXEL_COORDS[i][2]
                br, bg, bb = color_from_palette(current_palette, (seg * 51) & 0xFF)
                white_boost = int(180 * (intensity_sq ** 2))
                pixels[i] = (
                    min(255, int(br * intensity_sq) + white_boost),
                    min(255, int(bg * intensity_sq) + white_boost),
                    min(255, int(bb * intensity_sq) + white_boost),
                )
            else:
                pixels[i] = BLACK

    elif st.mode_idx == 5:
        # 5: 2D-Interferenz-Plasmafeld
        for i in range(NUM_PIXELS):
            _, _, nx, ny, r, _, seg = GEOM[i]
            v1 = math.sin(nx + phase_t * 2.1)
            v2 = math.sin(ny + phase_t * 1.7)
            v3 = math.sin((nx + ny + r * 0.12) - phase_t * 2.5)
            idx = int(((v1 + v2 + v3) * 0.16 + seg * 0.04) * 255) & 0xFF
            pixels[i] = color_from_palette(current_palette, idx, brightness=230)

    elif st.mode_idx == 6:
        # 6: Polar-Wirbelsturm
        angle_sweep = phase_t * 3.5
        for i in range(NUM_PIXELS):
            _, _, _, _, r, theta, _ = GEOM[i]
            wave = (math.sin(theta * 2.0 - angle_sweep + r * 0.15) + 1.0) * 0.5
            idx = int((theta / (2.0 * math.pi) + phase_t * 0.1) * 255) & 0xFF
            pixels[i] = color_from_palette(current_palette, idx, brightness=int(wave * 255))

    elif st.mode_idx == 7:
        # 7: Gravitations-Puls von der Sternspitze zur Basis
        y_front = Y_MAX - ((phase_t * 48.0) % 80.0)
        for i in range(NUM_PIXELS):
            _, y, _, _, _, _, seg = GEOM[i]
            dist_y = y - y_front
            if 0.0 <= dist_y < 22.0:
                val = 1.0 - (dist_y / 22.0)
                idx = int((seg * 0.08 + dist_y * 0.01) * 255) & 0xFF
                pixels[i] = color_from_palette(current_palette, idx, brightness=int(val * 255))
            else:
                pixels[i] = BLACK

    elif st.mode_idx == 8:
        # 8: Adventskranz (4 Kerzenzonen nacheinander + warmer weisser Stern)
        pixels.fill(BLACK)
        candles = int((phase_t % 16.0) // 4.0) + 1
        zones = (SEG_BOUGH_LOW, SEG_BOUGH_MID, SEG_BOUGH_HIGH)
        for z_idx in range(min(candles, 3)):
            start, end = SEGMENTS[zones[z_idx]]
            for i in range(start, end):
                flick = 0.72 + 0.28 * math.sin(phase_t * 6.5 + i * 1.3)
                pixels[i] = (int(255 * flick), int(125 * flick), int(14 * flick))
        if candles >= 4:
            s_start, s_end = SEGMENTS[SEG_STEM]
            for i in range(s_start, s_end):
                flick = 0.75 + 0.25 * math.sin(phase_t * 5.2 + i)
                pixels[i] = (int(180 * flick), int(95 * flick), int(15 * flick))
            st_start, st_end = SEGMENTS[SEG_STAR]
            for i in range(st_start, st_end):
                shim = 0.88 + 0.12 * math.sin(phase_t * 4.2 + i)
                pixels[i] = (int(255 * shim), int(240 * shim), int(205 * shim))

    elif st.mode_idx == 9:
        # 9: Schlittenfahrt durch die Sternennacht (X-Sweep + Silber-Gold-Glocken)
        sweep_x = (phase_t * 26.0) % (WIDTH_MM + 14.0) - 7.0
        bell_tick = int(phase_t * 5.0)
        bell_frac = (phase_t * 5.0) - bell_tick
        bell_a = (bell_tick * 23 + 7) % 50
        bell_b = (bell_tick * 37 + 19) % NUM_PIXELS
        bell_spark = (1.0 - bell_frac / 0.45) if bell_frac < 0.45 else 0.0
        for i in range(NUM_PIXELS):
            x = PIXEL_COORDS[i][0]
            r, g, b = 4, 10, 48
            dx = abs(x - sweep_x)
            if dx < 6.5:
                tr = 1.0 - dx / 6.5
                r = int(r + (255 - r) * tr)
                g = int(g + (225 - g) * tr)
                b = int(b + (140 - b) * tr)
            if bell_spark > 0.0 and (i == bell_a or i == bell_b):
                r = min(255, int(r + (255 - r) * bell_spark))
                g = min(255, int(g + (248 - g) * bell_spark))
                b = min(255, int(b + (210 - b) * bell_spark))
            pixels[i] = (r, g, b)

    elif st.mode_idx == 10:
        # 10: Stern von Bethlehem (Wegweiser in der Nacht)
        cycle = phase_t % 10.0
        breath = 0.55 + 0.45 * math.sin(phase_t * 3.1)
        beam_active = cycle >= 4.0
        p = (cycle - 4.0) / 6.0 if beam_active else 0.0
        beam_y = Y_MAX - p * (HEIGHT_MM + 12.0)
        cone_half = 0.45 + 0.35 * p

        for i in range(NUM_PIXELS):
            if i >= 50:
                if i in VIRTUAL_SEGMENTS[4]:  # VSEG_STAR_INNER
                    pixels[i] = (int(255 * breath), int(175 * breath), int(25 * breath))
                else:  # VSEG_STAR_OUTER
                    pixels[i] = (int(255 * breath), int(220 * breath), int(95 * breath))
            else:
                r, g, b = 6, 5, 4
                if beam_active:
                    x, y, _ = PIXEL_COORDS[i]
                    if y >= beam_y - 4.0:
                        ang = math.atan2(y - STAR_CY, x - STAR_CX)
                        ang_diff = abs(ang + 1.5707963)
                        cone = max(0.0, 1.0 - ang_diff / cone_half)
                        pool = max(0.0, (1.0 - y / 16.0) * (p - 0.55) * 2.2) if p > 0.55 and y < 16.0 else 0.0
                        glow = min(1.0, max(cone, pool))
                        r = int(6 + 249 * glow)
                        g = int(5 + 215 * glow)
                        b = int(4 + 135 * glow)
                pixels[i] = (r, g, b)

    elif st.mode_idx == 11:
        # 11: Kaminfeuer am Eisblick (ny < 0.45 Glut vs ny >= 0.45 Gletscher-Eis)
        for i in range(NUM_PIXELS):
            nx, ny = NORM_COORDS[i]
            if ny < 0.45:
                ember = (
                    0.50
                    + 0.30 * math.sin(phase_t * 3.8 + i * 1.7)
                    + 0.20 * math.sin(phase_t * 7.1 + nx * 9.0)
                )
                pixels[i] = (
                    min(255, int(255 * ember)),
                    min(255, int(75 * ember * ember + 25 * ember)),
                    int(6 * ember),
                )
            else:
                tw = max(0.0, math.sin(phase_t * 2.9 + i * 2.3 + nx * 11.0)) ** 10
                pixels[i] = (
                    12 + int(225 * tw),
                    42 + int(205 * tw),
                    72 + int(183 * tw),
                )

    else:
        # 12: Stille Nacht Atemzug (4s Einatmen, 1s Halten, 6s Ausatmen + Gamma-LUT)
        c = phase_t % 11.0
        if c < 4.0:
            raw_b = 0.5 - 0.5 * math.cos(math.pi * (c / 4.0))
        elif c < 5.0:
            raw_b = 1.0
        else:
            raw_b = 0.5 + 0.5 * math.cos(math.pi * ((c - 5.0) / 6.0))
        g_b = GAMMA_LUT[int(raw_b * 255)] / 255.0
        pilot_r, pilot_g, pilot_b = color_from_palette(PAL_FAIRY_LIGHT, 32)
        star_scale = 0.28 + 0.72 * g_b
        for i in range(NUM_PIXELS):
            if i >= 50:
                pixels[i] = (
                    int(pilot_r * star_scale),
                    int(pilot_g * star_scale),
                    int(pilot_b * star_scale),
                )
            else:
                pixels[i] = (
                    int(85 * g_b),
                    int((88 + 95 * g_b) * g_b),
                    int((12 + 48 * g_b) * g_b),
                )

    pixels.show()
    time.sleep(0.015)
