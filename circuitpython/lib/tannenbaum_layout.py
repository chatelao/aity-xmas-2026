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

TREE_TYPE_PCB = "PCB"
TREE_TYPE_HOLZ = "Holz"
TREE_TYPES = (TREE_TYPE_PCB, TREE_TYPE_HOLZ)

# --- 2. Logische Segment-IDs des Tannenbaums ---
SEG_BOUGH_LOW  = 0   # 18 LEDs: Unterer langer Tannenzweig (Basis)
SEG_BOUGH_MID  = 1   # 14 LEDs: Mittlerer geschwungener Tannenzweig
SEG_BOUGH_HIGH = 2   # 13 LEDs: Oberer Tannenzweig
SEG_STEM       = 3   # 5 LEDs:  Oberer Verbindungsbogen / Stiel unter dem Stern
SEG_STAR       = 4   # 10 LEDs: Stern an der Baumspitze (5 Innen- & 5 Aussen-LEDs)

# Segment-Bereiche als (start_index, end_index) fuer schnelles Slicing
SEGMENTS = (
    (0, 18),   # 0: SEG_BOUGH_LOW  (18 LEDs)
    (18, 32),  # 1: SEG_BOUGH_MID  (14 LEDs)
    (32, 45),  # 2: SEG_BOUGH_HIGH (13 LEDs)
    (45, 50),  # 3: SEG_STEM       (5 LEDs)
    (50, 60),  # 4: SEG_STAR       (10 LEDs)
)

# Physische LED-Index-Zuordnung je Baum-Variante:
# - PCB (Standard): 1:1 (0..59)
# - Holz: zweitlaengstes Segment (SEG_BOUGH_MID, 18..31) wird rueckwaerts angesteuert (31..18)
PIXEL_MAP_PCB = tuple(range(NUM_PIXELS))
PIXEL_MAP_HOLZ = tuple(
    (SEGMENTS[SEG_BOUGH_MID][0] + SEGMENTS[SEG_BOUGH_MID][1] - 1 - i)
    if SEGMENTS[SEG_BOUGH_MID][0] <= i < SEGMENTS[SEG_BOUGH_MID][1]
    else i
    for i in range(NUM_PIXELS)
)

SEGMENT_NAMES = (
    "Zweig Unten",
    "Zweig Mitte",
    "Zweig Oben",
    "Stiel / Verbindungsbogen",
    "Stern",
)

# --- 2b. Virtuelle Segmente (alle 6 logischen Segmente inkl. Stern Innen/Aussen) ---
VSEG_BOUGH_LOW  = 0  # 18 LEDs: Unterer langer Tannenzweig (0..17)
VSEG_BOUGH_MID  = 1  # 14 LEDs: Mittlerer geschwungener Tannenzweig (18..31)
VSEG_BOUGH_HIGH = 2  # 13 LEDs: Oberer Tannenzweig (32..44)
VSEG_STEM       = 3  # 5 LEDs:  Stiel / Verbindungsbogen (45..49)
VSEG_STAR_INNER = 4  # 5 LEDs:  Inneres Stern-Pentagon (im Uhrzeigersinn)
VSEG_STAR_OUTER = 5  # 5 LEDs:  Aeusseres Stern-Pentagon (im Uhrzeigersinn)

VIRTUAL_SEGMENTS = (
    tuple(range(0, 18)),   # 0: VSEG_BOUGH_LOW  (18 LEDs)
    tuple(range(18, 32)),  # 1: VSEG_BOUGH_MID  (14 LEDs)
    tuple(range(32, 45)),  # 2: VSEG_BOUGH_HIGH (13 LEDs)
    tuple(range(45, 50)),  # 3: VSEG_STEM       (5 LEDs)
    (50, 53, 54, 57, 58),  # 4: VSEG_STAR_INNER (5 LEDs)
    (51, 52, 55, 56, 59),  # 5: VSEG_STAR_OUTER (5 LEDs)
)

VIRTUAL_SEGMENT_NAMES = (
    "Zweig Unten",
    "Zweig Mitte",
    "Zweig Oben",
    "Stiel / Verbindungsbogen",
    "Stern Innen",
    "Stern Aussen",
)

# --- 3. Exakte PCB-Koordinaten (x_mm, y_mm, segment_id) fuer Index 0..59 ---
# Ursprung (0, 0) unten links, y nach oben wachsend (aus circuitpython/tannenbaum_leds.svg)
PIXEL_COORDS = (
    # Segment 0: (Unterer Zweig, rechts nach links)
    (38.862,  8.912, 0),  # Index 0 -> Ganz rechts
    (37.076,  6.998, 0),  # Index 1
    (35.100,  5.281, 0),  # Index 2
    (32.956,  3.781, 0),  # Index 3
    (30.667,  2.512, 0),  # Index 4
    (28.257,  1.491, 0),  # Index 5
    (25.754,  0.726, 0),  # Index 6
    (23.184,  0.227, 0),  # Index 7
    (20.577,  0.000, 0),  # Index 8 -> Tiefster Punkt
    (17.960,  0.046, 0),  # Index 9
    (15.362,  0.365, 0),  # Index 10
    (12.812,  0.955, 0),  # Index 11
    (10.337,  1.807, 0),  # Index 12
    ( 7.965,  2.914, 0),  # Index 13
    ( 5.722,  4.262, 0),  # Index 14
    ( 3.631,  5.838, 0),  # Index 15
    ( 1.717,  7.623, 0),  # Index 16
    ( 0.000,  9.599, 0),  # Index 17 -> Ganz links

    # Segment 1: (Mittlerer Zweig, rechts nach links-oben)
    (36.328, 14.954, 1),  # Index 18
    (33.885, 14.017, 1),  # Index 19
    (31.357, 13.340, 1),  # Index 20
    (28.773, 12.932, 1),  # Index 21
    (26.159, 12.796, 1),  # Index 22
    (23.546, 12.934, 1),  # Index 23
    (20.961, 13.344, 1),  # Index 24
    (18.434, 14.022, 1),  # Index 25
    (15.991, 14.961, 1),  # Index 26
    (13.660, 16.149, 1),  # Index 27
    (11.465, 17.576, 1),  # Index 28
    ( 9.432, 19.223, 1),  # Index 29
    ( 7.582, 21.074, 1),  # Index 30
    ( 5.936, 23.109, 1),  # Index 31

    # Segment 2: (Oberer Zweig, rechts nach links-oben)
    (36.468, 25.383, 2),  # Index 32
    (33.855, 25.247, 2),  # Index 33
    (31.243, 25.385, 2),  # Index 34
    (28.658, 25.795, 2),  # Index 35
    (26.131, 26.473, 2),  # Index 36
    (23.688, 27.412, 2),  # Index 37
    (21.357, 28.601, 2),  # Index 38
    (19.163, 30.027, 2),  # Index 39
    (17.130, 31.674, 2),  # Index 40
    (15.280, 33.525, 2),  # Index 41
    (13.634, 35.559, 2),  # Index 42
    (12.209, 37.754, 2),  # Index 43
    (11.022, 40.087, 2),  # Index 44

    # Segment 3: (Kurzer Bogen / Stiel unter dem Stern)
    (19.869, 39.313, 3),  # Index 45
    (21.903, 40.961, 3),  # Index 46
    (23.754, 42.812, 3),  # Index 47
    (25.401, 44.846, 3),  # Index 48
    (27.009, 46.640, 3),  # Index 49

    # Segment 4: (Stern, 5 Innen- & 5 Aussen-LEDs im Zickzack)
    (18.349, 58.095, 4),  # Index 50
    (17.189, 56.466, 4),  # Index 51
    (14.681, 63.964, 4),  # Index 52
    (16.589, 63.365, 4),  # Index 53
    (21.247, 66.711, 4),  # Index 54
    (21.207, 68.551, 4),  # Index 55 -> Hoechster Punkt (Spitze)
    (27.692, 64.094, 4),  # Index 56
    (25.796, 63.456, 4),  # Index 57
    (23.828, 57.956, 4),  # Index 58
    (25.013, 56.345, 4),  # Index 59
)

# --- 4. Geometrische Referenzpunkte & Bounding-Box (in mm) ---
X_MIN = 0.0
X_MAX = 38.862
Y_MIN = 0.0       # Baum-Basis unten
Y_MAX = 68.551    # Stern-Spitze oben

WIDTH_MM  = X_MAX - X_MIN  # 38.862 mm
HEIGHT_MM = Y_MAX - Y_MIN  # 68.551 mm

# Wichtige Ankerpunkte fuer Explosionen, Wellen & Polar-Effekte
CENTER_STAR = (21.1591, 61.9003)  # Exakter Mittelpunkt der 10 Stern-LEDs
CENTER_STEM = (23.754, 42.812)    # Mitte des Stiels
CENTER_TREE = (19.431, 34.2755)   # Geometrisches Zentrum der Bounding-Box
CENTER_BASE = (20.577, 12.796)    # Zentrum der unteren Zweig-Boegen

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


_pixels = None
_tree_type = TREE_TYPE_PCB


def normalize_tree_type(tree_type=None):
    """Normalisiert 'PCB' oder 'Holz' (Default: aktueller Baum-Typ, initial 'PCB')."""
    if tree_type is None:
        return _tree_type
    t = str(tree_type).strip().lower()
    if t == "holz":
        return TREE_TYPE_HOLZ
    if t == "pcb":
        return TREE_TYPE_PCB
    raise ValueError("Unbekannter Tannenbaum-Typ: {!r} (erwartet 'PCB' oder 'Holz')".format(tree_type))


def get_tree_type():
    """Gibt den aktiven Tannenbaum-Typ zurueck ('PCB' oder 'Holz')."""
    return _tree_type


def set_tree_type(tree_type):
    """Setzt den aktiven Tannenbaum-Typ ('PCB' oder 'Holz')."""
    global _tree_type
    _tree_type = normalize_tree_type(tree_type)
    return _tree_type


def get_pixel_map(tree_type=None):
    """Gibt die 60er Index-Zuordnungstabelle fuer 'PCB' oder 'Holz' zurueck."""
    if normalize_tree_type(tree_type) == TREE_TYPE_HOLZ:
        return PIXEL_MAP_HOLZ
    return PIXEL_MAP_PCB


def map_pixel_index(idx, tree_type=None):
    """Bildet einen logischen LED-Index (0..59) auf den physischen LED-Index ab."""
    if normalize_tree_type(tree_type) == TREE_TYPE_HOLZ:
        return PIXEL_MAP_HOLZ[idx]
    return idx


class MappedPixels:
    """Wrapper um NeoPixel, der je nach Baum-Typ ('PCB' vs. 'Holz') Indizes abbildet."""

    def __init__(self, pixels_obj, tree_type=None):
        self._px = pixels_obj
        self._fixed_tree_type = None if tree_type is None else normalize_tree_type(tree_type)

    def _map(self, idx):
        t = self._fixed_tree_type if self._fixed_tree_type is not None else _tree_type
        if t == TREE_TYPE_HOLZ:
            return PIXEL_MAP_HOLZ[idx]
        return idx

    def __len__(self):
        return len(self._px)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return [self._px[self._map(i)] for i in range(*idx.indices(len(self._px)))]
        return self._px[self._map(idx)]

    def __setitem__(self, idx, color):
        if isinstance(idx, slice):
            for i, c in zip(range(*idx.indices(len(self._px))), color):
                self._px[self._map(i)] = c
        else:
            self._px[self._map(idx)] = color

    def fill(self, color):
        self._px.fill(color)

    def show(self):
        # Rueckgabewert durchreichen (im Browser-Simulator ist show() awaitable)
        return self._px.show()

    def deinit(self):
        self._px.deinit()

    @property
    def brightness(self):
        return self._px.brightness

    @brightness.setter
    def brightness(self, value):
        self._px.brightness = value

    @property
    def auto_write(self):
        return self._px.auto_write

    @auto_write.setter
    def auto_write(self, value):
        self._px.auto_write = value

    def __getattr__(self, name):
        return getattr(self._px, name)


def wrap_pixels(pixels_obj, tree_type=None):
    """Umschliesst ein bestehendes NeoPixel-Objekt mit dem Baum-Typ-Mapping."""
    if isinstance(pixels_obj, MappedPixels):
        if tree_type is not None:
            pixels_obj._fixed_tree_type = normalize_tree_type(tree_type)
        return pixels_obj
    return MappedPixels(pixels_obj, tree_type=tree_type)


def set_pixels(pixels_obj):
    """Registriert das NeoPixel-Objekt einmalig fuer fill_seg(), fill_vseg() und VirtualSegment()."""
    global _pixels
    _pixels = pixels_obj


def init_pixels(brightness=0.3, auto_write=False, pixel_order=None, tree_type=None):
    """Initialisiert den NeoPixel-Streifen (60 LEDs an PIN_NEOPIXEL) und registriert ihn."""
    import neopixel

    if tree_type is not None:
        set_tree_type(tree_type)
    if pixel_order is None:
        pixel_order = neopixel.GRB
    px = neopixel.NeoPixel(
        PIN_NEOPIXEL,
        NUM_PIXELS,
        brightness=brightness,
        auto_write=auto_write,
        pixel_order=pixel_order,
    )
    mapped = MappedPixels(px)
    set_pixels(mapped)
    return mapped


class Button:
    """Kapselt Pull-Up-Setup, Aktiv-Low-Logik, Entprellung und Flankenerkennung."""

    def __init__(self, pin, debounce_s=0.05):
        import digitalio

        self._io = digitalio.DigitalInOut(pin)
        self._io.switch_to_input(pull=digitalio.Pull.UP)
        self._debounce_s = debounce_s
        self._last_state = False
        self._last_edge = -debounce_s

    @property
    def value(self):
        """Rohwert des Pins (True = losgelassen, False = gedrueckt)."""
        return self._io.value

    @property
    def is_pressed(self):
        """True solange der Taster gedrueckt ist (Aktiv-Low gegen GND)."""
        return not self._io.value

    def pressed(self):
        """True genau einmal pro Tastendruck (mit nicht-blockierender Entprellung)."""
        import time

        curr = self.is_pressed
        just_pressed = False
        if curr and not self._last_state:
            now = time.monotonic()
            if (now - self._last_edge) >= self._debounce_s:
                self._last_edge = now
                just_pressed = True
        self._last_state = curr
        return just_pressed


def init_buttons(debounce_s=0.05):
    """Initialisiert die beiden Taster D5 und D6 und gibt (btn_d5, btn_d6) zurueck."""
    return Button(PIN_BTN_A, debounce_s=debounce_s), Button(PIN_BTN_B, debounce_s=debounce_s)


def _require_pixels(pixels_obj):
    px = _pixels if pixels_obj is None else pixels_obj
    if px is None:
        raise RuntimeError("NeoPixel-Objekt fehlt: erst set_pixels(pixels) aufrufen.")
    return px


def fill_segment(pixels_obj, seg_id, color):
    """Faerbt ein einzelnes Segment (0..4) im NeoPixel-Puffer (ohne pixels.show() auszuloesen)."""
    start, end = SEGMENTS[seg_id]
    for i in range(start, end):
        pixels_obj[i] = color


def fill_seg(seg_id, color, pixels_obj=None):
    """Wie fill_segment(), nutzt aber das per set_pixels() registrierte Objekt."""
    fill_segment(_require_pixels(pixels_obj), seg_id, color)


def fill_virtual_segment(pixels_obj, vseg_id, color):
    """Faerbt ein virtuelles Segment (0..5, inkl. Stern Innen/Aussen) ohne pixels.show()."""
    for i in VIRTUAL_SEGMENTS[vseg_id]:
        pixels_obj[i] = color


def fill_vseg(vseg_id, color, pixels_obj=None):
    """Wie fill_virtual_segment(), nutzt aber das per set_pixels() registrierte Objekt."""
    fill_virtual_segment(_require_pixels(pixels_obj), vseg_id, color)


class VirtualSegment:
    """Adressiert ein beliebiges der 6 virtuellen Segmente wie einen eigenen Mini-Strip."""

    def __init__(self, vseg_or_pixels, vseg_id=None):
        if isinstance(vseg_or_pixels, int):
            self._pixels = _require_pixels(None)
            self.vseg_id = vseg_or_pixels
        else:
            self._pixels = vseg_or_pixels
            self.vseg_id = vseg_id
        self.indices = VIRTUAL_SEGMENTS[self.vseg_id]

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return [self._pixels[i] for i in self.indices[idx]]
        return self._pixels[self.indices[idx]]

    def __setitem__(self, idx, color):
        if isinstance(idx, slice):
            for i, c in zip(self.indices[idx], color):
                self._pixels[i] = c
        else:
            self._pixels[self.indices[idx]] = color

    def __iter__(self):
        return iter(self.indices)

    def fill(self, color):
        """Faerbt alle LEDs dieses virtuellen Segments (ohne pixels.show())."""
        for i in self.indices:
            self._pixels[i] = color


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
