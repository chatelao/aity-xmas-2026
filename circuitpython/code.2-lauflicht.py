# code.2-lauflicht.py
import time
from tannenbaum_layout import NUM_PIXELS, init_pixels, init_buttons

pixels = init_pixels(brightness=0.3)
btn_d5, btn_d6 = init_buttons()

SPEEDS = (0.08, 0.04, 0.015)  # Sekunden pro Schritt
speed_idx = 1
direction = 1
head = 0
last_step = time.monotonic()

while True:
    now = time.monotonic()

    # Taster D5: Richtung umkehren
    if btn_d5.pressed():
        direction *= -1

    # Taster D6: Geschwindigkeit wechseln
    if btn_d6.pressed():
        speed_idx = (speed_idx + 1) % len(SPEEDS)

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
