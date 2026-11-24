# code.1c-one-LED.py
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6
# Abhaengigkeiten: /lib/neopixel.mpy, /lib/tannenbaum_layout.py

import time
import neopixel
from tannenbaum_layout import NUM_PIXELS, init_pixels, init_buttons

pixels = init_pixels(brightness=0.2, pixel_order=neopixel.GRB)
btn_d5, btn_d6 = init_buttons()

RED = (255, 0, 0)
OFF = (0, 0, 0)
STEP_INTERVAL = 1.0  # 1 Sekunde pro Schritt

pos = 0
direction = 1  # Standard: aufwaerts (aufsteigend)
last_step = time.monotonic()


def render():
    pixels.fill(OFF)
    pixels[pos] = RED
    pixels.show()


render()

while True:
    now = time.monotonic()

    # D5: Richtung aufwaerts + sofort einen Schritt hoch
    if btn_d5.pressed():
        direction = 1
        pos = (pos + direction) % NUM_PIXELS
        last_step = now
        render()

    # D6: Richtung abwaerts + sofort einen Schritt runter
    if btn_d6.pressed():
        direction = -1
        pos = (pos + direction) % NUM_PIXELS
        last_step = now
        render()

    # Automatisch jede Sekunde einen Schritt in der letzten Richtung
    if (now - last_step) >= STEP_INTERVAL:
        last_step = now
        pos = (pos + direction) % NUM_PIXELS
        render()

    time.sleep(0.02)
