# code.1-one-LED-auto.py
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6
# Abhaengigkeiten: /lib/neopixel.mpy, /lib/tannenbaum_layout.py

import time
import neopixel
from tannenbaum_layout import NUM_PIXELS, init_pixels

pixels = init_pixels(brightness=0.2, pixel_order=neopixel.GRB)

RED = (255, 0, 0)
OFF = (0, 0, 0)
STEP_INTERVAL = 1.0  # 1 Sekunde pro Schritt

pos = 0
last_step = time.monotonic()


def render():
    pixels.fill(OFF)
    pixels[pos] = RED
    pixels.show()


render()

while True:
    now = time.monotonic()

    # Automatisch jede Sekunde einen Schritt vorwaerts
    if (now - last_step) >= STEP_INTERVAL:
        last_step = now
        pos = (pos + 1) % NUM_PIXELS
        render()

    time.sleep(0.02)
