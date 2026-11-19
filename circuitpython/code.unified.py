# code.unified.py
# Unified Firmware: Alle Tannenbaum-Animationen in einem Skript
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6
# Abhaengigkeiten: /lib/neopixel.mpy, /lib/tannenbaum_layout.py, /lib/tannenbaum_palettes.py
#
# Steuerung ueber D5 (Zurueck / Langsamer) & D6 (Vor / Schneller):
# - Einzelklick (Single Tap): Farbpalette wechseln (D5: vorherige, D6: naechste)
# - Doppelklick (Double Tap): Modus wechseln (D5: vorheriger, D6: naechster)
# - Gedrueckt halten (Long Hold): Geschwindigkeit anpassen (D5: langsamer, D6: schneller)

import time
import math
import digitalio
import neopixel
from tannenbaum_layout import (
    NUM_PIXELS, PIN_NEOPIXEL, PIN_BTN_A, PIN_BTN_B,
    PIXEL_COORDS, CENTER_TREE, POLAR_TREE, Y_MAX,
    EPICENTERS, VIRTUAL_SEGMENTS, build_distance_lut,
)
from tannenbaum_palettes import (
    PALETTES, PALETTE_NAMES, PAL_FAIRY_LIGHT,
    color_from_palette, blend_palette_toward, render_twinkle_tree,
)

# --- Hardware-Setup ---
pixels = neopixel.NeoPixel(
    PIN_NEOPIXEL, NUM_PIXELS, brightness=0.35, auto_write=False, pixel_order=neopixel.GRB
)

btn_d5 = digitalio.DigitalInOut(PIN_BTN_A)
btn_d5.switch_to_input(pull=digitalio.Pull.UP)

btn_d6 = digitalio.DigitalInOut(PIN_BTN_B)
btn_d6.switch_to_input(pull=digitalio.Pull.UP)

# --- Geometrie-Vorberechnung ---
DIST_LUT = tuple(build_distance_lut(ep) for ep in EPICENTERS)
CX, CY = CENTER_TREE
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

# --- Zustand ---
mode_idx = 0
pal_idx = 0
speed_idx = DEFAULT_SPEED_IDX

current_palette = PALETTES[pal_idx]
target_palette = PALETTES[pal_idx]

# Animations-Zustand
last_now = time.monotonic()
phase_t = 0.0
chase_head = 0
chase_accum = 0.0
seg_active = 0
seg_accum = 0.0
wave_epi = 0
wave_radius = 0.0


def reset_mode_state():
    global chase_accum, seg_accum, wave_radius
    pixels.fill((0, 0, 0))
    chase_accum = 0.0
    seg_accum = 0.0
    wave_radius = 0.0


print("=== AITY XMAS 2026 UNIFIED FIRMWARE ===")
print("Double Tap D5/D6: Modus | Single Tap D5/D6: Palette | Long Hold D5/D6: Tempo")
print(f"Modus: {MODE_NAMES[mode_idx]} | Palette: {PALETTE_NAMES[pal_idx]} | Tempo: {SPEED_FACTORS[speed_idx]}x")

while True:
    now = time.monotonic()
    dt = now - last_now
    if dt < 0.0:
        dt = 0.0
    elif dt > 0.2:
        dt = 0.2
    last_now = now

    # --- Taster-Gesten auswerten ---
    for ev in gest_d5.update(now):
        if ev == "double_tap":
            mode_idx = (mode_idx - 1) % NUM_MODES
            reset_mode_state()
            print(f"Modus: {MODE_NAMES[mode_idx]}")
        elif ev == "single_tap":
            pal_idx = (pal_idx - 1) % len(PALETTES)
            target_palette = PALETTES[pal_idx]
            print(f"Palette: {PALETTE_NAMES[pal_idx]}")
        elif ev == "long_hold":
            if speed_idx > 0:
                speed_idx -= 1
                print(f"Tempo: {SPEED_FACTORS[speed_idx]}x (Stufe {speed_idx}/8)")

    for ev in gest_d6.update(now):
        if ev == "double_tap":
            mode_idx = (mode_idx + 1) % NUM_MODES
            reset_mode_state()
            print(f"Modus: {MODE_NAMES[mode_idx]}")
        elif ev == "single_tap":
            pal_idx = (pal_idx + 1) % len(PALETTES)
            target_palette = PALETTES[pal_idx]
            print(f"Palette: {PALETTE_NAMES[pal_idx]}")
        elif ev == "long_hold":
            if speed_idx < len(SPEED_FACTORS) - 1:
                speed_idx += 1
                print(f"Tempo: {SPEED_FACTORS[speed_idx]}x (Stufe {speed_idx}/8)")

    # Sanfter Paletten-Uebergang
    if current_palette != target_palette:
        current_palette = blend_palette_toward(current_palette, target_palette, 18)

    speed_factor = SPEED_FACTORS[speed_idx]
    phase_t += dt * speed_factor

    # --- Aktiven Modus rendern ---
    if mode_idx == 0:
        # 0: TwinkleFOX
        render_twinkle_tree(
            pixels,
            int(now * 1000),
            current_palette,
            star_palette=PAL_FAIRY_LIGHT,
            speed=speed_idx,
            density=5,
        )

    elif mode_idx == 1:
        # 1: Sechs LEDs (statisch aus aktiver Palette)
        pixels.fill((0, 0, 0))
        for i in range(6):
            pixels[i] = color_from_palette(current_palette, i * 42)

    elif mode_idx == 2:
        # 2: Lauflicht mit Schweif
        chase_accum += dt * speed_factor
        if chase_accum >= 0.04:
            chase_accum = 0.0
            for i in range(NUM_PIXELS):
                r, g, b = pixels[i]
                pixels[i] = (r >> 1, g >> 1, b >> 1)
            pixels[chase_head] = color_from_palette(current_palette, (chase_head * 4) & 0xFF)
            chase_head = (chase_head + 1) % NUM_PIXELS

    elif mode_idx == 3:
        # 3: Segmente durchlaufen
        seg_accum += dt * speed_factor
        if seg_accum >= 0.6:
            seg_accum = 0.0
            seg_active = (seg_active + 1) % len(VIRTUAL_SEGMENTS)
        pixels.fill((0, 0, 0))
        col = color_from_palette(current_palette, (seg_active * 42) & 0xFF)
        for i in VIRTUAL_SEGMENTS[seg_active]:
            pixels[i] = col

    elif mode_idx == 4:
        # 4: Koordinaten-Wellenexplosion
        wave_radius += dt * 45.0 * speed_factor
        if wave_radius > 95.0:
            wave_radius = 0.0
            wave_epi = (wave_epi + 1) % len(EPICENTERS)
        dists = DIST_LUT[wave_epi]
        wave_width = 9.0
        for i in range(NUM_PIXELS):
            d = abs(dists[i] - wave_radius)
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
                pixels[i] = (0, 0, 0)

    elif mode_idx == 5:
        # 5: 2D-Interferenz-Plasmafeld
        for i in range(NUM_PIXELS):
            _, _, nx, ny, r, _, seg = GEOM[i]
            v1 = math.sin(nx + phase_t * 2.1)
            v2 = math.sin(ny + phase_t * 1.7)
            v3 = math.sin((nx + ny + r * 0.12) - phase_t * 2.5)
            idx = int(((v1 + v2 + v3) * 0.16 + seg * 0.04) * 255) & 0xFF
            pixels[i] = color_from_palette(current_palette, idx, brightness=230)

    elif mode_idx == 6:
        # 6: Polar-Wirbelsturm
        angle_sweep = phase_t * 3.5
        for i in range(NUM_PIXELS):
            _, _, _, _, r, theta, _ = GEOM[i]
            wave = (math.sin(theta * 2.0 - angle_sweep + r * 0.15) + 1.0) * 0.5
            idx = int((theta / (2.0 * math.pi) + phase_t * 0.1) * 255) & 0xFF
            pixels[i] = color_from_palette(current_palette, idx, brightness=int(wave * 255))

    else:
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
                pixels[i] = (0, 0, 0)

    pixels.show()
    time.sleep(0.015)
