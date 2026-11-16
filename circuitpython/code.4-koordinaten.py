# code.4-koordinaten.py
import time
import math
import board
import digitalio
import neopixel

NUM_PIXELS = 60
pixels = neopixel.NeoPixel(board.D10, NUM_PIXELS, brightness=0.35, auto_write=False, pixel_order=neopixel.GRB)

btn_d5 = digitalio.DigitalInOut(board.D5)
btn_d5.switch_to_input(pull=digitalio.Pull.UP)
btn_d6 = digitalio.DigitalInOut(board.D6)
btn_d6.switch_to_input(pull=digitalio.Pull.UP)

# (x, y, segment_id) fuer D201 bis D260
LED_DATA = (
    (138.72, -32.16, 0), (132.25, -29.55, 0), (125.69, -32.27, 0), (129.38, -38.15, 0), (136.13, -39.87, 0),
    (136.81, -32.78, 1), (132.25, -27.55, 1), (127.59, -32.89, 1), (128.20, -39.77, 1), (134.88, -38.28, 1),
    (147.35, -81.29, 2), (144.91, -82.23, 2), (142.38, -82.91, 2), (139.80, -83.32, 2), (137.19, -83.45, 2),
    (134.57, -83.32, 2), (131.99, -82.91, 2), (129.46, -82.23, 2), (127.02, -81.29, 2), (124.69, -80.11, 2),
    (122.49, -78.68, 2), (120.46, -77.03, 2), (118.61, -75.18, 2), (116.96, -73.15, 2), (149.88, -87.33, 3),
    (148.09, -89.24, 3), (146.12, -90.96, 3), (143.97, -92.46, 3), (141.69, -93.73, 3), (139.28, -94.75, 3),
    (136.77, -95.51, 3), (134.21, -96.01, 3), (131.60, -96.24, 3), (128.98, -96.20, 3), (126.39, -95.88, 3),
    (123.84, -95.29, 3), (121.36, -94.44, 3), (118.99, -93.33, 3), (116.75, -91.98, 3), (114.66, -90.41, 3),
    (112.74, -88.62, 3), (111.03, -86.65, 3), (147.50, -70.87, 4), (144.88, -71.01, 4), (142.27, -70.87, 4),
    (139.68, -70.46, 4), (137.16, -69.78, 4), (134.71, -68.85, 4), (132.38, -67.66, 4), (130.19, -66.23, 4),
    (128.15, -64.59, 4), (126.30, -62.74, 4), (124.66, -60.70, 4), (123.23, -58.51, 4), (122.04, -56.18, 4),
    (138.01, -49.61, 5), (136.40, -51.40, 5), (134.75, -53.43, 5), (132.90, -55.28, 5), (130.87, -56.93, 5)
)

# Epizentren: 0 = Stern oben, 1 = Stiel Mitte, 2 = Bogen unten
EPICENTERS = (
    (132.25, -33.70),
    (134.75, -53.43),
    (134.57, -83.32)
)

SEG_BASE_COLOR = (
    (255, 60, 0), (255, 180, 0), (0, 255, 100),
    (0, 160, 255), (140, 0, 255), (255, 0, 120)
)

# Distanzen einmalig vorberechnen (verhindert math.sqrt in der Render-Schleife)
DIST_LUT = []
for ex, ey in EPICENTERS:
    dists = tuple(math.sqrt((x - ex) ** 2 + (y - ey) ** 2) for x, y, _ in LED_DATA)
    DIST_LUT.append(dists)

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
            seg = LED_DATA[i][2]
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
