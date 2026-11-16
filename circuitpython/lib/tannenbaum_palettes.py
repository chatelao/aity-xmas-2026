# /lib/tannenbaum_palettes.py
"""
FastLED 'TwinkleFOX.ino' Paletten- und Glitzer-Engine fuer CircuitPython.
Optimiert fuer das 60-LED Tannenbaum-Board (XIAO RP2040 / XIAO ESP32-C6).
"""

# --- 1. Basis-Farbkonstanten aus TwinkleFOX.ino (RGB) ---
RED        = (255, 0, 0)
GREEN      = (0, 255, 0)
BLUE       = (0, 0, 255)
WHITE      = (255, 255, 255)
BLACK      = (0, 0, 0)

# Spezielle Glühlampen- und Weihnachtsfarben (Mark Kriegsman / FastLED)
C9_RED     = (184, 4, 0)
C9_ORANGE  = (144, 44, 2)
C9_GREEN   = (4, 98, 2)
C9_BLUE    = (7, 7, 88)
C9_WHITE   = (224, 160, 64)

FAIRY_FULL = (255, 157, 42)   # 0xFFE42D korrigiert fuer NeoPixel
FAIRY_HALF = (127, 78, 21)
FAIRY_QTR  = (63, 39, 10)

HOLLY_GRN  = (0, 88, 12)
HOLLY_RED  = (176, 4, 2)

SNOW_WHITE = (224, 240, 255)
SNOW_HALF  = (48, 56, 64)
ICE_BLUE1  = (12, 60, 180)
ICE_BLUE2  = (24, 128, 255)
ICE_BLUE3  = (160, 220, 255)

# --- 2. Die 8 TwinkleFOX 16-Eintrags-Paletten ---
# Jede Palette hat exakt 16 Stuetzstellen fuer schnelles Bit-Shift-Indexing (0..15)

# 0: Klassische amerikanische C9-Weihnachtsbaumkerzen (5 Farben)
PAL_RETRO_C9 = (
    C9_RED, C9_ORANGE, C9_RED, C9_ORANGE,
    C9_ORANGE, C9_RED, C9_ORANGE, C9_RED,
    C9_GREEN, C9_GREEN, C9_GREEN, C9_GREEN,
    C9_BLUE, C9_BLUE, C9_BLUE, C9_WHITE
)

# 1: Stechpalme (Dominantes Tannengruen mit einzelnen roten Beeren)
PAL_HOLLY = (
    HOLLY_GRN, HOLLY_GRN, HOLLY_GRN, HOLLY_GRN,
    HOLLY_GRN, HOLLY_GRN, HOLLY_GRN, HOLLY_GRN,
    HOLLY_GRN, HOLLY_GRN, HOLLY_GRN, HOLLY_GRN,
    HOLLY_GRN, HOLLY_GRN, HOLLY_GRN, HOLLY_RED
)

# 2: Warmweisse Lichterkette (Fairy Lights) mit dynamischer Helligkeitsstufung
PAL_FAIRY_LIGHT = (
    FAIRY_FULL, FAIRY_FULL, FAIRY_FULL, FAIRY_FULL,
    FAIRY_HALF, FAIRY_HALF, FAIRY_FULL, FAIRY_FULL,
    FAIRY_QTR, FAIRY_QTR, FAIRY_FULL, FAIRY_FULL,
    FAIRY_FULL, FAIRY_FULL, FAIRY_FULL, FAIRY_FULL
)

# 3: Rot & Grün mit Schnee-Akzenten (Klassischer Weihnachtsbaum)
PAL_RED_GREEN_WHITE = (
    RED, RED, RED, RED,
    RED, RED, RED, GREEN,
    GREEN, GREEN, GREEN, GREEN,
    GREEN, GREEN, WHITE, WHITE
)

# 4: Zuckerstange (Rot & Weiss)
PAL_RED_WHITE = (
    RED, RED, RED, RED,
    RED, RED, RED, RED,
    WHITE, WHITE, WHITE, WHITE,
    WHITE, WHITE, WHITE, WHITE
)

# 5: Glitzernder Neuschnee
PAL_SNOW = (
    SNOW_HALF, SNOW_HALF, SNOW_HALF, SNOW_HALF,
    SNOW_HALF, SNOW_HALF, SNOW_HALF, SNOW_HALF,
    SNOW_HALF, SNOW_HALF, SNOW_HALF, SNOW_HALF,
    SNOW_HALF, SNOW_HALF, SNOW_HALF, SNOW_WHITE
)

# 6: Gefrorener Eisbaum (Blau- & Cyan-Stufen)
PAL_ICE = (
    ICE_BLUE1, ICE_BLUE1, ICE_BLUE1, ICE_BLUE1,
    ICE_BLUE1, ICE_BLUE1, ICE_BLUE1, ICE_BLUE1,
    ICE_BLUE2, ICE_BLUE2, ICE_BLUE2, ICE_BLUE2,
    ICE_BLUE2, ICE_BLUE3, ICE_BLUE3, SNOW_WHITE
)

# 7: Blaue Winternacht mit weissen Sternen
PAL_BLUE_WHITE = (
    BLUE, BLUE, BLUE, BLUE,
    BLUE, BLUE, BLUE, BLUE,
    BLUE, BLUE, BLUE, BLUE,
    BLUE, WHITE, WHITE, WHITE
)

# Alle Paletten in einer Liste zum Durchschalten per Taster D5/D6
PALETTES = (
    PAL_RETRO_C9,
    PAL_HOLLY,
    PAL_FAIRY_LIGHT,
    PAL_RED_GREEN_WHITE,
    PAL_RED_WHITE,
    PAL_SNOW,
    PAL_ICE,
    PAL_BLUE_WHITE,
)

PALETTE_NAMES = (
    "Retro C9",
    "Holly (Tannengruen & Beeren)",
    "Fairy Light (Warmes Gold)",
    "Rot-Gruen-Weiss",
    "Zuckerstange (Rot-Weiss)",
    "Glitzerschnee",
    "Eis-Kristall",
    "Blaue Winternacht",
)

# Dezente Hintergrundfarbe fuer nicht aktive Funkel-Pixel (wie in TwinkleFOX)
BG_DARK_GREEN = (0, 5, 1)
BG_WARM_DARK  = (8, 4, 1)
BG_BLACK      = (0, 0, 0)


# --- 3. FastLED Paletten-Interpolation & Wellenfunktionen ---
def color_from_palette(palette16, index, brightness=255, blend=True):
    """
    Liest eine Farbe aus einer 16-Eintrags-Palette ueber einen 8-Bit-Index (0..255).
    Entspricht FastLEDs ColorFromPalette().
    """
    idx = int(index) & 0xFF
    slot = idx >> 4            # Obere 4 Bit: Eintrag 0..15
    frac = (idx & 0x0F) << 4   # Untere 4 Bit skaliert auf 0..240

    c1 = palette16[slot]
    if not blend or frac == 0:
        r, g, b = c1
    else:
        c2 = palette16[(slot + 1) & 0x0F]
        inv = 256 - frac
        r = (c1[0] * inv + c2[0] * frac) >> 8
        g = (c1[1] * inv + c2[1] * frac) >> 8
        b = (c1[2] * inv + c2[2] * frac) >> 8

    if brightness < 255:
        b_scale = (int(brightness) & 0xFF) + 1
        r = (r * b_scale) >> 8
        g = (g * b_scale) >> 8
        b = (b * b_scale) >> 8

    return (r, g, b)


def attack_decay_wave8(i):
    """
    Dreieckswelle aus TwinkleFOX.ino:
    Schnelles Aufgluehen (0..85 -> 0..255) und doppelt so langsames Abkuehlen (86..255 -> 255..0).
    """
    i = int(i) & 0xFF
    if i < 86:
        return i * 3
    i -= 86
    return 255 - (i + (i >> 1))


def cool_like_incandescent(rgb, phase):
    """
    Simuliert das physikalische Abkuehlen eines Gluehdrahts (Rotverschiebung beim Ausdimmen).
    """
    if phase < 128:
        return rgb
    cooling = ((phase - 128) * 2) & 0xFF
    r, g, b = rgb
    g = (g * (256 - (cooling >> 1))) >> 8
    b = (b * (256 - cooling)) >> 8
    return (r, g, b)


# --- 4. Die TwinkleFOX-Kernfunktion fuer ein einzelnes Pixel ---
def compute_one_twinkle(ms, salt, palette16, speed=4, density=5, cool_incandescent=True, bg_color=BG_BLACK):
    """
    Berechnet deterministisch den Funkel-Zustand eines Pixels zum Zeitpunkt `ms` (Millisekunden)
    und dem Pixel-Index `salt` (0..59). Benötigt kein Zustands-Array im RAM!
    - speed:   0 (sehr langsam) bis 8 (sehr schnell), Standard = 4
    - density: 0 (kaum Funkeln) bis 8 (alle LEDs funkeln dauerhaft), Standard = 5
    """
    # 16-Bit Pseudo-Zufallsgenerator (identische Konstanten wie Mark Kriegsman)
    prng16 = ((salt + 1) * 2053 + 1384) & 0xFFFF
    my_clock30 = (ms >> (8 - speed)) & 0x3FFFFFFF

    # Jedes Pixel erhaelt sein eigenes Tempo (Clock-Multiplier) und Phasen-Offset
    clock_offset = prng16
    prng16 = (prng16 * 2053 + 1384) & 0xFFFF
    speed_mult = ((((prng16 & 0xFF) >> 4) + (prng16 & 0x0F)) & 0x0F) + 0x08

    my_clock = ((my_clock30 * speed_mult) >> 3) + clock_offset
    my_unique8 = (prng16 >> 8) & 0xFF

    # Ticks bestimmen den aktuellen Lebenszyklus des Funkens
    ticks = (my_clock >> 8) & 0xFFFF
    phase = my_clock & 0xFF

    # Neuer PRNG-Hash fuer genau diesen Funken-Zyklus
    wave_hash = ((ticks * 2053) + 1384 + my_unique8) & 0xFFFF
    deltabright = (wave_hash >> 8) & 0xFF
    color_index = wave_hash & 0xFF

    # Pruefen, ob das Pixel in diesem Zyklus ueberhaupt aufleuchtet (Dichte-Schwelle)
    threshold = 255 - (density * 28)
    if deltabright >= threshold:
        brightness = attack_decay_wave8(phase)
        c = color_from_palette(palette16, color_index, brightness, blend=False)
        if cool_incandescent:
            c = cool_like_incandescent(c, phase)
        return c

    return bg_color


# --- 5. High-Level Helfer fuer das gesamte Tannenbaum-Board ---
def render_twinkle_tree(pixels_obj, ms, branch_palette, star_palette=None, speed=4, density=5, bg_color=BG_BLACK):
    """
    Rendert den gesamten 60-LED-Tannenbaum mit einem einzigen Funktionsaufruf.
    Optional kann der Stern an der Spitze (Pixel 0..9) eine eigene Palette erhalten!
    """
    if star_palette is None:
        star_palette = branch_palette

    for i in range(len(pixels_obj)):
        pal = star_palette if i < 10 else branch_palette
        pixels_obj[i] = compute_one_twinkle(
            ms, i, pal, speed=speed, density=density, bg_color=bg_color
        )
