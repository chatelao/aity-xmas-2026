# code.5-maximal.py
import time
import math
import digitalio
import neopixel
from tannenbaum_layout import (
    NUM_PIXELS, PIN_NEOPIXEL, PIN_BTN_A, PIN_BTN_B,
    PIXEL_COORDS, CENTER_TREE, POLAR_TREE, Y_MAX, hsv_to_rgb_gamma,
)

pixels = neopixel.NeoPixel(PIN_NEOPIXEL, NUM_PIXELS, brightness=0.4, auto_write=False, pixel_order=neopixel.GRB)

btn_d5 = digitalio.DigitalInOut(PIN_BTN_A)
btn_d5.switch_to_input(pull=digitalio.Pull.UP)
btn_d6 = digitalio.DigitalInOut(PIN_BTN_B)
btn_d6.switch_to_input(pull=digitalio.Pull.UP)

# Geometrie-Vorberechnung relativ zum Baum-Zentrum CENTER_TREE
CX, CY = CENTER_TREE
GEOM = tuple(
    (x, y, (x - CX) * 0.08, (y - CY) * 0.08, r, theta, seg)
    for (x, y, seg), (r, theta) in zip(PIXEL_COORDS, POLAR_TREE)
)

mode = 0
palette_shift = 0.0
last_d5 = True
last_d6 = True
t0 = time.monotonic()

while True:
    t = time.monotonic() - t0
    curr_d5 = btn_d5.value
    curr_d6 = btn_d6.value

    if not curr_d5 and last_d5:
        mode = (mode + 1) % 3
    last_d5 = curr_d5

    if not curr_d6 and last_d6:
        palette_shift = (palette_shift + 0.25) % 1.0
    last_d6 = curr_d6

    if mode == 0:
        # Modus 0: 2D-Interferenz-Plasmafeld
        for i in range(NUM_PIXELS):
            _, _, nx, ny, r, _, seg = GEOM[i]
            v1 = math.sin(nx + t * 2.1)
            v2 = math.sin(ny + t * 1.7)
            v3 = math.sin((nx + ny + r * 0.12) - t * 2.5)
            hue = ((v1 + v2 + v3) * 0.16 + palette_shift + seg * 0.04) % 1.0
            pixels[i] = hsv_to_rgb_gamma(hue, 0.95, 0.9)

    elif mode == 1:
        # Modus 1: Polar-Wirbelsturm mit Segment-Puls
        angle_sweep = t * 3.5
        for i in range(NUM_PIXELS):
            _, _, _, _, r, theta, seg = GEOM[i]
            wave = (math.sin(theta * 2.0 - angle_sweep + r * 0.15) + 1.0) * 0.5
            hue = (theta / (2.0 * math.pi) + palette_shift + t * 0.1) % 1.0
            pixels[i] = hsv_to_rgb_gamma(hue, 0.9, wave)

    else:
        # Modus 2: Gravitations-Puls von der Sternspitze (Y_MAX) zur Basis (Y_MIN)
        y_front = Y_MAX - ((t * 48.0) % 80.0)
        for i in range(NUM_PIXELS):
            _, y, _, _, _, _, seg = GEOM[i]
            dist_y = y - y_front
            if 0.0 <= dist_y < 22.0:
                val = 1.0 - (dist_y / 22.0)
                hue = (palette_shift + seg * 0.08 + dist_y * 0.01) % 1.0
                pixels[i] = hsv_to_rgb_gamma(hue, 0.85, val)
            else:
                pixels[i] = (0, 0, 0)

    pixels.show()
