# code.7-twinkle.py
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6
# Abhaengigkeiten: /lib/neopixel.mpy, /lib/tannenbaum_layout.py, /lib/tannenbaum_palettes.py

import time
import digitalio
import neopixel
from tannenbaum_layout import NUM_PIXELS, PIN_NEOPIXEL, PIN_BTN_A, PIN_BTN_B
from tannenbaum_palettes import (
    PALETTES, PALETTE_NAMES, PAL_FAIRY_LIGHT,
    blend_palette_toward, render_twinkle_tree,
)

pixels = neopixel.NeoPixel(
    PIN_NEOPIXEL, NUM_PIXELS, brightness=0.35, auto_write=False, pixel_order=neopixel.GRB
)

btn_d5 = digitalio.DigitalInOut(PIN_BTN_A)
btn_d5.switch_to_input(pull=digitalio.Pull.UP)
btn_d6 = digitalio.DigitalInOut(PIN_BTN_B)
btn_d6.switch_to_input(pull=digitalio.Pull.UP)

SECONDS_PER_PALETTE = 30
SPEED_PRESETS = (
    (3, 4, "Sanft"),
    (4, 5, "Standard"),
    (6, 7, "Lebhaft"),
)

pal_idx = 0
spd_idx = 1
current_palette = PALETTES[pal_idx]
target_palette = PALETTES[pal_idx]
last_switch = time.monotonic()
last_d5 = True
last_d6 = True

print("TwinkleFOX Palette:", PALETTE_NAMES[pal_idx])

while True:
    now = time.monotonic()
    curr_d5 = btn_d5.value
    curr_d6 = btn_d6.value

    # D5 oder Timer: Naechste Farbpalette weich ueberblenden
    if (not curr_d5 and last_d5) or (now - last_switch >= SECONDS_PER_PALETTE):
        pal_idx = (pal_idx + 1) % len(PALETTES)
        target_palette = PALETTES[pal_idx]
        last_switch = now
        print("TwinkleFOX Palette:", PALETTE_NAMES[pal_idx])
    last_d5 = curr_d5

    # D6: Tempo / Dichte umschalten
    if not curr_d6 and last_d6:
        spd_idx = (spd_idx + 1) % len(SPEED_PRESETS)
        print("TwinkleFOX Tempo:", SPEED_PRESETS[spd_idx][2])
    last_d6 = curr_d6

    if current_palette != target_palette:
        current_palette = blend_palette_toward(current_palette, target_palette, 18)

    speed, density, _ = SPEED_PRESETS[spd_idx]
    ms = int(now * 1000)
    render_twinkle_tree(
        pixels,
        ms,
        current_palette,
        star_palette=PAL_FAIRY_LIGHT,
        speed=speed,
        density=density,
    )
    pixels.show()
    time.sleep(0.02)
