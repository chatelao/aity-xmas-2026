# code.7-koordinaten.py
import time
from tannenbaum_layout import (
    NUM_PIXELS, PIXEL_COORDS, EPICENTERS,
    init_pixels, init_buttons, build_distance_lut,
)

pixels = init_pixels(brightness=0.35)
btn_d5, btn_d6 = init_buttons()

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

while True:
    now = time.monotonic()

    if btn_d5.pressed():
        t_explosion = now

    if btn_d6.pressed():
        epi_idx = (epi_idx + 1) % len(EPICENTERS)
        t_explosion = now

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
