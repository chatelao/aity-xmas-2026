# code.2-one-LED-taster.py
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6
# Abhaengigkeiten: /lib/neopixel.mpy, /lib/tannenbaum_layout.py, /lib/tannenbaum_palettes.py

import time
import neopixel
from tannenbaum_layout import NUM_PIXELS, init_pixels, init_buttons
from tannenbaum_palettes import RED, BLACK

pixels = init_pixels(brightness=0.2, pixel_order=neopixel.GRB)
btn_d5, btn_d6 = init_buttons()

pos = 0


def render():
    pixels.fill(BLACK)
    pixels[pos] = RED
    pixels.show()


render()

while True:
    # D5: Eine Position hoch (0 -> 59 -> 0)
    if btn_d5.pressed():
        pos = (pos + 1) % NUM_PIXELS
        render()

    # D6: Eine Position runter (0 -> 59 -> 58 ...)
    if btn_d6.pressed():
        pos = (pos - 1) % NUM_PIXELS
        render()

    time.sleep(0.02)
