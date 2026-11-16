# code.3-segmente.py
import time
import digitalio
import neopixel
from tannenbaum_layout import (
    NUM_PIXELS, PIN_NEOPIXEL, PIN_BTN_A, PIN_BTN_B,
    VIRTUAL_SEGMENTS, set_pixels, fill_vseg,
)

pixels = neopixel.NeoPixel(PIN_NEOPIXEL, NUM_PIXELS, brightness=0.25, auto_write=False, pixel_order=neopixel.GRB)
set_pixels(pixels)

btn_d5 = digitalio.DigitalInOut(PIN_BTN_A)
btn_d5.switch_to_input(pull=digitalio.Pull.UP)
btn_d6 = digitalio.DigitalInOut(PIN_BTN_B)
btn_d6.switch_to_input(pull=digitalio.Pull.UP)

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
last_d5 = True
last_d6 = True
last_tick = time.monotonic()

def show_segment(seg_idx):
    pixels.fill((0, 0, 0))
    fill_vseg(seg_idx, SEG_COLORS[seg_idx])
    pixels.show()

show_segment(active_seg)

while True:
    now = time.monotonic()
    curr_d5 = btn_d5.value
    curr_d6 = btn_d6.value

    # D5: Umschalten Auto / Manuell
    if not curr_d5 and last_d5:
        auto_mode = not auto_mode
    last_d5 = curr_d5

    # D6: Manuelles Weiterschalten
    if not curr_d6 and last_d6:
        auto_mode = False
        active_seg = (active_seg + 1) % len(VIRTUAL_SEGMENTS)
        show_segment(active_seg)
    last_d6 = curr_d6

    # Automatik-Zyklus alle 0.6 Sekunden
    if auto_mode and (now - last_tick) >= 0.6:
        last_tick = now
        active_seg = (active_seg + 1) % len(VIRTUAL_SEGMENTS)
        show_segment(active_seg)
