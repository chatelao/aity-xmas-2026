# code.6-segmente.py
import time
from tannenbaum_layout import (
    VIRTUAL_SEGMENTS, init_pixels, init_buttons, fill_vseg,
)
from tannenbaum_palettes import (
    BLACK, ICE_BLUE2, LIGHT_GREEN, SOFT_VIOLET, MAGENTA, C9_RED, FAIRY_FULL,
)

pixels = init_pixels(brightness=0.25)
btn_d5, btn_d6 = init_buttons()

SEG_COLORS = (
    ICE_BLUE2,    # VSeg 0: Zweig Unten (Eisblau)
    LIGHT_GREEN,  # VSeg 1: Zweig Mitte (Hellgruen)
    SOFT_VIOLET,  # VSeg 2: Zweig Oben (Violett)
    MAGENTA,      # VSeg 3: Stiel (Magenta)
    C9_RED,       # VSeg 4: Stern Innen (C9-Rot)
    FAIRY_FULL,   # VSeg 5: Stern Aussen (Warmes Gold)
)

active_seg = 0
auto_mode = True
last_tick = time.monotonic()


def show_segment(seg_idx):
    pixels.fill(BLACK)
    fill_vseg(seg_idx, SEG_COLORS[seg_idx])
    pixels.show()


show_segment(active_seg)

while True:
    now = time.monotonic()

    # D5: Umschalten Auto / Manuell
    if btn_d5.pressed():
        auto_mode = not auto_mode

    # D6: Manuelles Weiterschalten
    if btn_d6.pressed():
        auto_mode = False
        active_seg = (active_seg + 1) % len(VIRTUAL_SEGMENTS)
        show_segment(active_seg)

    # Automatik-Zyklus alle 0.6 Sekunden
    if auto_mode and (now - last_tick) >= 0.6:
        last_tick = now
        active_seg = (active_seg + 1) % len(VIRTUAL_SEGMENTS)
        show_segment(active_seg)
