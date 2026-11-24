# code.3-segmente.py
import time
from tannenbaum_layout import (
    VIRTUAL_SEGMENTS, init_pixels, init_buttons, fill_vseg,
)

pixels = init_pixels(brightness=0.25)
btn_d5, btn_d6 = init_buttons()

SEG_COLORS = (
    (0, 180, 255),   # VSeg 0: Zweig Unten (Eisblau)
    (0, 255, 80),    # VSeg 1: Zweig Mitte (Smaragdgruen)
    (120, 0, 255),   # VSeg 2: Zweig Oben (Violett)
    (255, 0, 140),   # VSeg 3: Stiel (Pink)
    (255, 40, 0),    # VSeg 4: Stern Innen (Feuerrot)
    (255, 180, 0),   # VSeg 5: Stern Aussen (Goldgelb)
)

active_seg = 0
auto_mode = True
last_tick = time.monotonic()


def show_segment(seg_idx):
    pixels.fill((0, 0, 0))
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
