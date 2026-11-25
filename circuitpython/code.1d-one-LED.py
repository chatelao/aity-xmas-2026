# code.1d-one-LED.py
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6
# Abhaengigkeiten: /lib/neopixel.mpy

import time
import board
import digitalio
import neopixel

NUM_PIXELS = 60
DEBOUNCE_S = 0.05

pixels = neopixel.NeoPixel(
    board.D10,
    NUM_PIXELS,
    brightness=0.2,
    auto_write=False,
    pixel_order=neopixel.GRB,
)

btn_d5 = digitalio.DigitalInOut(board.D5)
btn_d5.switch_to_input(pull=digitalio.Pull.UP)

btn_d6 = digitalio.DigitalInOut(board.D6)
btn_d6.switch_to_input(pull=digitalio.Pull.UP)

RED = (255, 0, 0)
OFF = (0, 0, 0)

pos = 0
last_d5 = False
last_d6 = False
last_edge_d5 = -DEBOUNCE_S
last_edge_d6 = -DEBOUNCE_S


def render():
    pixels.fill(OFF)
    pixels[pos] = RED
    pixels.show()


render()

while True:
    now = time.monotonic()

    # D5: Eine Position hoch (0 -> 59 -> 0)
    curr_d5 = not btn_d5.value
    if curr_d5 and not last_d5 and (now - last_edge_d5) >= DEBOUNCE_S:
        last_edge_d5 = now
        pos = (pos + 1) % NUM_PIXELS
        render()
    last_d5 = curr_d5

    # D6: Eine Position runter (0 -> 59 -> 58 ...)
    curr_d6 = not btn_d6.value
    if curr_d6 and not last_d6 and (now - last_edge_d6) >= DEBOUNCE_S:
        last_edge_d6 = now
        pos = (pos - 1) % NUM_PIXELS
        render()
    last_d6 = curr_d6

    time.sleep(0.02)
