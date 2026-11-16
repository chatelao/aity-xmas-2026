# code.4-koordinaten.py
import time
import digitalio
import neopixel
from tannenbaum_layout import (
    NUM_PIXELS, PIN_NEOPIXEL, PIN_BTN_A, PIN_BTN_B,
    PIXEL_COORDS, EPICENTERS, build_distance_lut,
)

pixels = neopixel.NeoPixel(PIN_NEOPIXEL, NUM_PIXELS, brightness=0.35, auto_write=False, pixel_order=neopixel.GRB)

btn_d5 = digitalio.DigitalInOut(PIN_BTN_A)
btn_d5.switch_to_input(pull=digitalio.Pull.UP)
btn_d6 = digitalio.DigitalInOut(PIN_BTN_B)
btn_d6.switch_to_input(pull=digitalio.Pull.UP)

SEG_BASE_COLOR = (
    (0, 160, 255),   # Seg 0: Zweig Unten
    (0, 255, 100),   # Seg 1: Zweig Mitte
    (140, 0, 255),   # Seg 2: Zweig Oben
    (255, 0, 120),   # Seg 3: Stiel
    (255, 140, 0),   # Seg 4: Stern
)

# Distanzen einmalig vorberechnen (verhindert math.sqrt in der Render-Schleife)
DIST_LUT = tuple(build_distance_lut(ep) for ep in EPICENTERS)

epi_idx = 0
t_explosion = time.monotonic()
WAVE_SPEED = 45.0   # mm pro Sekunde
WAVE_WIDTH = 9.0    # Halbwertsbreite der Wellenfront in mm

last_d5 = True
last_d6 = True

while True:
    now = time.monotonic()
    curr_d5 = btn_d5.value
    curr_d6 = btn_d6.value

    if not curr_d5 and last_d5:
        t_explosion = now
    last_d5 = curr_d5

    if not curr_d6 and last_d6:
        epi_idx = (epi_idx + 1) % len(EPICENTERS)
        t_explosion = now
    last_d6 = curr_d6

    radius = (now - t_explosion) * WAVE_SPEED
    if radius > 95.0:
        # Automatischer Neustart nach Durchlauf
        t_explosion = now
        radius = 0.0

    dists = DIST_LUT[epi_idx]
    for i in range(NUM_PIXELS):
        d = abs(dists[i] - radius)
        if d < WAVE_WIDTH:
            # Dreiecks-Pulsform + weisser Wellenkamm
            intensity = 1.0 - (d / WAVE_WIDTH)
            intensity_sq = intensity * intensity
            seg = PIXEL_COORDS[i][2]
            br, bg, bb = SEG_BASE_COLOR[seg]
            # Kern der Welle blitzt weiss auf
            white_boost = int(180 * (intensity_sq ** 2))
            r = min(255, int(br * intensity_sq) + white_boost)
            g = min(255, int(bg * intensity_sq) + white_boost)
            b = min(255, int(bb * intensity_sq) + white_boost)
            pixels[i] = (r, g, b)
        else:
            pixels[i] = (0, 0, 0)

    pixels.show()
