# code.0-one-LED.py
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6
# Abhaengigkeiten: /lib/neopixel.mpy, /lib/tannenbaum_layout.py

import time
from tannenbaum_layout import NUM_PIXELS, init_pixels, init_buttons

pixels = init_pixels(brightness=0.2)
btn_d5, btn_d6 = init_buttons()

RED = (255, 0, 0)
OFF = (0, 0, 0)

pos = 0


def render():
    pixels.fill(OFF)
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
