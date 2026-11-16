# code.2-lauflicht.py
import time
import board
import digitalio
import neopixel

NUM_PIXELS = 60
pixels = neopixel.NeoPixel(board.D10, NUM_PIXELS, brightness=0.3, auto_write=False, pixel_order=neopixel.GRB)

btn_d5 = digitalio.DigitalInOut(board.D5)
btn_d5.switch_to_input(pull=digitalio.Pull.UP)
btn_d6 = digitalio.DigitalInOut(board.D6)
btn_d6.switch_to_input(pull=digitalio.Pull.UP)

SPEEDS = (0.08, 0.04, 0.015)  # Sekunden pro Schritt
speed_idx = 1
direction = 1
head = 0

last_d5 = True
last_d6 = True
last_step = time.monotonic()

while True:
    now = time.monotonic()

    # Taster D5: Richtung umkehren
    curr_d5 = btn_d5.value
    if not curr_d5 and last_d5:
        direction *= -1
    last_d5 = curr_d5

    # Taster D6: Geschwindigkeit wechseln
    curr_d6 = btn_d6.value
    if not curr_d6 and last_d6:
        speed_idx = (speed_idx + 1) % len(SPEEDS)
    last_d6 = curr_d6

    # Zeitgesteuerter Animationsschritt (kein blockierendes sleep!)
    if (now - last_step) >= SPEEDS[speed_idx]:
        last_step = now

        # Bestehende Pixel abdunkeln (Schweif-Effekt durch Bit-Shift / Integer-Mathematik)
        for i in range(NUM_PIXELS):
            r, g, b = pixels[i]
            pixels[i] = (r >> 1, g >> 1, b >> 1)

        # Kopf-Pixel neu setzen
        pixels[head] = (0, 220, 255)
        pixels.show()

        head = (head + direction) % NUM_PIXELS
