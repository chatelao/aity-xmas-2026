# code.3-segmente.py
import time
import board
import digitalio
import neopixel

NUM_PIXELS = 60
pixels = neopixel.NeoPixel(board.D10, NUM_PIXELS, brightness=0.25, auto_write=False, pixel_order=neopixel.GRB)

btn_d5 = digitalio.DigitalInOut(board.D5)
btn_d5.switch_to_input(pull=digitalio.Pull.UP)
btn_d6 = digitalio.DigitalInOut(board.D6)
btn_d6.switch_to_input(pull=digitalio.Pull.UP)

# Exakte Segmentgrenzen aus den KiCad-Koordinaten (inklusiver Start, exklusives Ende)
SEGMENTS = (
    (0, 5),    # Seg 0: D201-D205 (Pentagon innen)
    (5, 10),   # Seg 1: D206-D210 (Pentagon aussen)
    (10, 24),  # Seg 2: D211-D224 (Mittlerer Bogen)
    (24, 42),  # Seg 3: D225-D242 (Unterer Bogen)
    (42, 55),  # Seg 4: D243-D255 (Oberer Bogen)
    (55, 60)   # Seg 5: D256-D260 (Stiel)
)

SEG_COLORS = (
    (255, 40, 0),    # Seg 0: Feuerrot
    (255, 180, 0),   # Seg 1: Goldgelb
    (0, 255, 80),    # Seg 2: Smaragdgruen
    (0, 180, 255),   # Seg 3: Eisblau
    (120, 0, 255),   # Seg 4: Violett
    (255, 0, 140)    # Seg 5: Pink
)

active_seg = 0
auto_mode = True
last_d5 = True
last_d6 = True
last_tick = time.monotonic()

def show_segment(seg_idx):
    pixels.fill((0, 0, 0))
    start, end = SEGMENTS[seg_idx]
    color = SEG_COLORS[seg_idx]
    for i in range(start, end):
        pixels[i] = color
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
        active_seg = (active_seg + 1) % len(SEGMENTS)
        show_segment(active_seg)
    last_d6 = curr_d6

    # Automatik-Zyklus alle 0.6 Sekunden
    if auto_mode and (now - last_tick) >= 0.6:
        last_tick = now
        active_seg = (active_seg + 1) % len(SEGMENTS)
        show_segment(active_seg)
