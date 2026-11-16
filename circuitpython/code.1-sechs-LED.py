# code.1-sechs-LED.py
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6
# Abhaengigkeiten: /lib/neopixel.mpy

import time
import board
import digitalio
import neopixel

# --- Hardware-Konfiguration ---
NUM_PIXELS = 60
# Hinweis: Echte WS2811 nutzen oft neopixel.RGB, WS2812B-Derivate neopixel.GRB
PIXEL_ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    board.D10,
    NUM_PIXELS,
    brightness=0.2,
    auto_write=False,
    pixel_order=PIXEL_ORDER
)

btn_d5 = digitalio.DigitalInOut(board.D5)
btn_d5.switch_to_input(pull=digitalio.Pull.UP)

btn_d6 = digitalio.DigitalInOut(board.D6)
btn_d6.switch_to_input(pull=digitalio.Pull.UP)

# --- Statische Farbtabelle (Tupel spart RAM) ---
PRIMARY_3 = (
    (255, 0, 0),    # D201: Rot
    (0, 255, 0),    # D202: Gruen
    (0, 0, 255),    # D203: Blau
)

SECONDARY_3 = (
    (255, 255, 0),  # D204: Gelb
    (0, 255, 255),  # D205: Cyan
    (255, 0, 255),  # D206: Magenta
)

show_six = False
last_d5 = True

def render():
    pixels.fill((0, 0, 0))
    for i in range(3):
        pixels[i] = PRIMARY_3[i]
    if show_six:
        for i in range(3):
            pixels[i + 3] = SECONDARY_3[i]
    pixels.show()

render()

while True:
    curr_d5 = btn_d5.value
    # Flankenerkennung (Taster gegen GND = False)
    if not curr_d5 and last_d5:
        show_six = not show_six
        render()
        time.sleep(0.05)  # Entprellung
    last_d5 = curr_d5

    # D6: Alle LEDs dunkel schalten solange gedrueckt
    if not btn_d6.value:
        pixels.fill((0, 0, 0))
        pixels.show()
    else:
        render()
    time.sleep(0.02)
