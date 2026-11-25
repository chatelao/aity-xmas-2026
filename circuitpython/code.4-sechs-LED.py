# code.4-sechs-LED.py
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6
# Abhaengigkeiten: /lib/neopixel.mpy, /lib/tannenbaum_layout.py, /lib/tannenbaum_palettes.py

import time
from tannenbaum_layout import init_pixels, init_buttons
from tannenbaum_palettes import RED, GREEN, BLUE, BLACK

pixels = init_pixels(brightness=0.2)
btn_d5, btn_d6 = init_buttons()

# --- Statische Farbtabelle (Tupel spart RAM) ---
PRIMARY_3 = (
    RED,    # D201: Rot
    GREEN,  # D202: Gruen
    BLUE,   # D203: Blau
)

SECONDARY_3 = (
    (255, 255, 0),  # D204: Gelb
    (0, 255, 255),  # D205: Cyan
    (255, 0, 255),  # D206: Magenta
)

show_six = False


def render():
    pixels.fill(BLACK)
    for i in range(3):
        pixels[i] = PRIMARY_3[i]
    if show_six:
        for i in range(3):
            pixels[i + 3] = SECONDARY_3[i]
    pixels.show()


render()

while True:
    if btn_d5.pressed():
        show_six = not show_six
        render()

    # D6: Alle LEDs dunkel schalten solange gedrueckt
    if btn_d6.is_pressed:
        pixels.fill(BLACK)
        pixels.show()
    else:
        render()
    time.sleep(0.02)
