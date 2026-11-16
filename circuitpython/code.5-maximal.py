# code.5-maximal.py
import time
import math
import board
import digitalio
import neopixel

NUM_PIXELS = 60
pixels = neopixel.NeoPixel(board.D10, NUM_PIXELS, brightness=0.4, auto_write=False, pixel_order=neopixel.GRB)

btn_d5 = digitalio.DigitalInOut(board.D5)
btn_d5.switch_to_input(pull=digitalio.Pull.UP)
btn_d6 = digitalio.DigitalInOut(board.D6)
btn_d6.switch_to_input(pull=digitalio.Pull.UP)

RAW_COORDS = (
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

# Gamma-LUT (Gamma = 2.6) fuer saubere Farbmischung
GAMMA = tuple(int(((i / 255.0) ** 2.6) * 255.0 + 0.5) for i in range(256))

# Geometrie-Vorberechnung relativ zum Zentrum (cx=130.5, cy=-61.9)
CX, CY = 130.5, -61.9
GEOM = []
for x, y, seg in RAW_COORDS:
    dx = x - CX
    dy = y - CY
    r = math.sqrt(dx * dx + dy * dy)
    theta = math.atan2(dy, dx)  # [-pi, +pi]
    GEOM.append((x, y, dx * 0.08, dy * 0.08, r, theta, seg))
GEOM = tuple(GEOM)

def hsv_to_grb_gamma(h, s, v):
    """Schnelle HSV->RGB Konvertierung (h, s, v in 0.0..1.0) inkl. Gamma."""
    h = (h % 1.0) * 6.0
    i = int(h)
    f = h - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    if i == 0: r, g, b = v, t, p
    elif i == 1: r, g, b = q, v, p
    elif i == 2: r, g, b = p, v, t
    elif i == 3: r, g, b = p, q, v
    elif i == 4: r, g, b = t, p, v
    else: r, g, b = v, p, q
    return (GAMMA[int(r * 255)], GAMMA[int(g * 255)], GAMMA[int(b * 255)])

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
            pixels[i] = hsv_to_grb_gamma(hue, 0.95, 0.9)

    elif mode == 1:
        # Modus 1: Polar-Wirbelsturm mit Segment-Puls
        angle_sweep = t * 3.5
        for i in range(NUM_PIXELS):
            _, _, _, _, r, theta, seg = GEOM[i]
            wave = (math.sin(theta * 2.0 - angle_sweep + r * 0.15) + 1.0) * 0.5
            hue = (theta / (2.0 * math.pi) + palette_shift + t * 0.1) % 1.0
            pixels[i] = hsv_to_grb_gamma(hue, 0.9, wave)

    else:
        # Modus 2: Gravitations-Puls von der Sternspitze (y=-27.5) zum Bogen (y=-96.2)
        y_front = -27.5 - ((t * 48.0) % 80.0)
        for i in range(NUM_PIXELS):
            _, y, _, _, _, _, seg = GEOM[i]
            dist_y = y - y_front
            if 0.0 <= dist_y < 22.0:
                val = 1.0 - (dist_y / 22.0)
                hue = (palette_shift + seg * 0.08 + dist_y * 0.01) % 1.0
                pixels[i] = hsv_to_grb_gamma(hue, 0.85, val)
            else:
                pixels[i] = (0, 0, 0)

    pixels.show()
