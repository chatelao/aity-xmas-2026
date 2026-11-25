# code.0-one-LED.py
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6
# Abhaengigkeiten: /lib/neopixel.mpy, /lib/tannenbaum_layout.py

import time
from tannenbaum_layout import init_pixels

pixels = init_pixels(brightness=0.2)

pixels[0] = (255, 0, 0)
pixels.show()

while True:
    time.sleep(1)
