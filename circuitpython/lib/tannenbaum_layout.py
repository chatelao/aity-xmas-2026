# /lib/tannenbaum_layout.py
"""
Geometrie-, Koordinaten- und Segment-Bibliothek fuer das 60-LED Tannenbaum-PCB.
Kompatibel mit Seeed Studio XIAO RP2040 und XIAO ESP32-C6 unter CircuitPython.
"""

import math
import board

# --- 1. Hardware-Konstanten ---
NUM_PIXELS = 60
PIN_NEOPIXEL = board.D10
PIN_BTN_A = board.D5
PIN_BTN_B = board.D6

# --- 2. Logische Segment-IDs des Tannenbaums ---
SEG_STAR_INNER = 0   # 5 LEDs:  Inneres Pentagon an der Baumspitze
SEG_STAR_OUTER = 1   # 5 LEDs:  Aeusseres Pentagon an der Baumspitze
SEG_BOUGH_MID  = 2   # 14 LEDs: Mittlerer geschwungener Tannenzweig
SEG_BOUGH_LOW  = 3   # 18 LEDs: Unterer langer Tannenzweig (Basis)
SEG_BOUGH_HIGH = 4   # 13 LEDs: Oberer Tannenzweig
SEG_STEM       = 5   # 5 LEDs:  Oberer Verbindungsbogen / Stiel unter dem Stern

# Segment-Bereiche als (start_index, end_index) fuer schnelles Slicing
SEGMENTS = (
    (0, 5),    # 0: SEG_STAR_INNER (5 LEDs)
    (5, 10),   # 1: SEG_STAR_OUTER (5 LEDs)
    (10, 24),  # 2: SEG_BOUGH_MID  (14 LEDs)
    (24, 42),  # 3: SEG_BOUGH_LOW  (18 LEDs)
    (42, 55),  # 4: SEG_BOUGH_HIGH (13 LEDs)
    (55, 60),  # 5: SEG_STEM       (5 LEDs)
)

SEGMENT_NAMES = (
    "Stern Innen",
    "Stern Aussen",
    "Zweig Mitte",
    "Zweig Unten",
    "Zweig Oben",
    "Stiel / Verbindungsbogen",
)

# --- 3. Exakte PCB-Koordinaten (x_mm, y_mm, segment_id) fuer Index 0..59 ---
PIXEL_COORDS = (
    # Segment 0: (Stern Innen)
    (138.7170, -32.1639, 0),  # Index 0
    (132.2500, -29.5500, 0),  # Index 1
    (125.6868, -32.2740, 0),  # Index 2
    (129.3756, -38.1534, 0),  # Index 3
    (136.1286, -39.8746, 0),  # Index 4

    # Segment 1: (Stern Aussen)
    (136.8149, -32.7819, 1),  # Index 5
    (132.2500, -27.5500, 1),  # Index 6 -> Hoechster Punkt (Spitze)
    (127.5889, -32.8920, 1),  # Index 7
    (128.2000, -39.7714, 1),  # Index 8
    (134.8820, -38.2811, 1),  # Index 9

    # Segment 2: (Mittlerer Zweig, rechts nach links-oben)
    (147.3545, -81.2933, 2),  # Index 10
    (144.9116, -82.2311, 2),  # Index 11
    (142.3839, -82.9084, 2),  # Index 12
    (139.7993, -83.3177, 2),  # Index 13
    (137.1861, -83.4547, 2),  # Index 14
    (134.5729, -83.3177, 2),  # Index 15
    (131.9883, -82.9084, 2),  # Index 16
    (129.4607, -82.2311, 2),  # Index 17
    (127.0177, -81.2933, 2),  # Index 18
    (124.6861, -80.1053, 2),  # Index 19
    (122.4915, -78.6801, 2),  # Index 20
    (120.4579, -77.0333, 2),  # Index 21
    (118.6075, -75.1829, 2),  # Index 22
    (116.9607, -73.1493, 2),  # Index 23

    # Segment 3: (Unterer Zweig, rechts nach links)
    (149.8776, -87.3257, 3),  # Index 24 -> Ganz rechts
    (148.0930, -89.2395, 3),  # Index 25
    (146.1180, -90.9563, 3),  # Index 26
    (143.9745, -92.4572, 3),  # Index 27
    (141.6858, -93.7259, 3),  # Index 28
    (139.2770, -94.7483, 3),  # Index 29
    (136.7746, -95.5134, 3),  # Index 30
    (134.2058, -96.0127, 3),  # Index 31
    (131.5990, -96.2408, 3),  # Index 32 -> Tiefster Punkt
    (128.9826, -96.1951, 3),  # Index 33
    (126.3853, -95.8762, 3),  # Index 34
    (123.8356, -95.2876, 3),  # Index 35
    (121.3613, -94.4356, 3),  # Index 36
    (118.9897, -93.3297, 3),  # Index 37
    (116.7467, -91.9820, 3),  # Index 38
    (114.6568, -90.4071, 3),  # Index 39
    (112.7430, -88.6225, 3),  # Index 40
    (111.0262, -86.6476, 3),  # Index 41 -> Ganz links

    # Segment 4: (Oberer Zweig, rechts nach links-oben)
    (147.4950, -70.8705, 4),  # Index 42
    (144.8818, -71.0075, 4),  # Index 43
    (142.2686, -70.8705, 4),  # Index 44
    (139.6840, -70.4612, 4),  # Index 45
    (137.1564, -69.7839, 4),  # Index 46
    (134.7134, -68.8461, 4),  # Index 47
    (132.3818, -67.6581, 4),  # Index 48
    (130.1872, -66.2329, 4),  # Index 49
    (128.1535, -64.5861, 4),  # Index 50
    (126.3032, -62.7357, 4),  # Index 51
    (124.6564, -60.7021, 4),  # Index 52
    (123.2312, -58.5075, 4),  # Index 53
    (122.0432, -56.1759, 4),  # Index 54

    # Segment 5: (Kurzer Bogen / Stiel unter dem Stern)
    (138.0086, -49.6069, 5),  # Index 55
    (136.4000, -51.4000, 5),  # Index 56
    (134.7532, -53.4336, 5),  # Index 57
    (132.9028, -55.2840, 5),  # Index 58
    (130.8692, -56.9308, 5),  # Index 59
)

# --- 4. Geometrische Referenzpunkte & Bounding-Box (in mm) ---
X_MIN = 111.0262
X_MAX = 149.8776
Y_MIN = -96.2408  # Baum-Basis unten
Y_MAX = -27.5500  # Stern-Spitze oben

WIDTH_MM  = X_MAX - X_MIN  # 38.8514 mm
HEIGHT_MM = Y_MAX - Y_MIN  # 68.6908 mm

# Wichtige Ankerpunkte fuer Explosionen, Wellen & Polar-Effekte
CENTER_STAR = (132.1894, -34.3292)  # Exakter Mittelpunkt der 10 Stern-LEDs
CENTER_STEM = (134.7532, -53.4336)  # Mitte des Stiels
CENTER_TREE = (130.4519, -61.8954)  # Geometrisches Zentrum der Bounding-Box
CENTER_BASE = (131.5990, -83.3177)  # Zentrum der unteren Zweig-Boegen

EPICENTERS = (
    CENTER_STAR,
    CENTER_STEM,
    CENTER_TREE,
    CENTER_BASE,
)

# --- 5. Vorberechnete Norm- und Polarkoordinaten (einmalig beim Import) ---
# NORM_COORDS[i] = (nx, ny) mit nx in [0.0..1.0] (links->rechts), ny in [0.0..1.0] (unten->oben)
NORM_COORDS = tuple(
    ((x - X_MIN) / WIDTH_MM, (y - Y_MIN) / HEIGHT_MM)
    for x, y, _ in PIXEL_COORDS
)

# POLAR_TREE[i] = (r_mm, theta_rad) relativ zum Baum-Zentrum CENTER_TREE
POLAR_TREE = tuple(
    (
        math.sqrt((x - CENTER_TREE[0]) ** 2 + (y - CENTER_TREE[1]) ** 2),
        math.atan2(y - CENTER_TREE[1], x - CENTER_TREE[0]),
    )
    for x, y, _ in PIXEL_COORDS
)

# POLAR_STAR[i] = (r_mm, theta_rad) relativ zum Stern-Zentrum CENTER_STAR
POLAR_STAR = tuple(
    (
        math.sqrt((x - CENTER_STAR[0]) ** 2 + (y - CENTER_STAR[1]) ** 2),
        math.atan2(y - CENTER_STAR[1], x - CENTER_STAR[0]),
    )
    for x, y, _ in PIXEL_COORDS
)

# Gamma-Lookup-Table (Gamma = 2.6) fuer lineare Helligkeitswahrnehmung
GAMMA_LUT = tuple(int(((i / 255.0) ** 2.6) * 255.0 + 0.5) for i in range(256))


# --- 6. Hilfsfunktionen fuer Animationen ---
def build_distance_lut(origin_xy):
    """
    Berechnet einmalig ein Tupel mit den 60 euklidischen Abstaenden (in mm)
    zu einem beliebigen Punkt (ox, oy). Verhindert math.sqrt() in der Hauptschleife.
    """
    ox, oy = origin_xy
    return tuple(math.sqrt((x - ox) ** 2 + (y - oy) ** 2) for x, y, _ in PIXEL_COORDS)


def fill_segment(pixels_obj, seg_id, color):
    """Faerbt ein einzelnes Segment (0..5) im NeoPixel-Puffer (ohne pixels.show() auszuloesen)."""
    start, end = SEGMENTS[seg_id]
    for i in range(start, end):
        pixels_obj[i] = color


def hsv_to_rgb_gamma(h, s, v):
    """Konvertiert HSV (0.0..1.0) in ein Gamma-korrigiertes RGB-Tupel (0..255)."""
    h = (h % 1.0) * 6.0
    i = int(h)
    f = h - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return (GAMMA_LUT[int(r * 255)], GAMMA_LUT[int(g * 255)], GAMMA_LUT[int(b * 255)])
