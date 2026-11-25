# code.9-twinkle.py
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6
# Abhaengigkeiten: /lib/neopixel.mpy, /lib/tannenbaum_layout.py, /lib/tannenbaum_palettes.py

import time
from tannenbaum_layout import init_pixels, init_buttons
from tannenbaum_palettes import (
    PALETTES, PALETTE_NAMES, PAL_FAIRY_LIGHT,
    blend_palette_toward, render_twinkle_tree,
)

pixels = init_pixels(brightness=0.35)
btn_d5, btn_d6 = init_buttons()

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

print("TwinkleFOX Palette:", PALETTE_NAMES[pal_idx])

while True:
    now = time.monotonic()

    # D5 oder Timer: Naechste Farbpalette weich ueberblenden
    if btn_d5.pressed() or (now - last_switch >= SECONDS_PER_PALETTE):
        pal_idx = (pal_idx + 1) % len(PALETTES)
        target_palette = PALETTES[pal_idx]
        last_switch = now
        print("TwinkleFOX Palette:", PALETTE_NAMES[pal_idx])

    # D6: Tempo / Dichte umschalten
    if btn_d6.pressed():
        spd_idx = (spd_idx + 1) % len(SPEED_PRESETS)
        print("TwinkleFOX Tempo:", SPEED_PRESETS[spd_idx][2])

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
