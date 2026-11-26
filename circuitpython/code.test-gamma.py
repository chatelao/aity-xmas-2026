# code.test-gamma.py - CIE-L*, Gamma & Weissabgleich-Kalibrierung auf echter Hardware
# Hardware: Seeed XIAO RP2040 / XIAO ESP32-C6, Abhaengigkeiten: /lib/neopixel.mpy, /lib/tannenbaum_layout.py
#
# Zeigt eine Helligkeitsrampe ueber alle 60 LEDs. Eine gut korrigierte Rampe sieht GLEICHMAESSIG
# aus (jede LED ein gleich grosser Helligkeitsschritt) und Weiss wirkt neutral (nicht gruenstichig).
# Taster A wechselt die Kurve (CIE L* / gamma 1.0 / 2.2 / 2.6 / 2.8),
# Taster B schaltet den WS2812B-Weissabgleich (255, 176, 240) EIN / AUS.
import time
from tannenbaum_layout import (
    NUM_PIXELS, WHITE_BALANCE, init_pixels, init_buttons, build_rgb_luts,
)
import tannenbaum_layout as tl

pixels = init_pixels(brightness=1.0)
btn_a, btn_b = init_buttons()

MODES = (
    ("CIE L*", "cie_lstar", 2.6),
    ("gamma 1.0", "gamma", 1.0),
    ("gamma 2.2", "gamma", 2.2),
    ("gamma 2.6", "gamma", 2.6),
    ("gamma 2.8", "gamma", 2.8),
)
m_idx = 0
wb_on = True


def draw():
    label, curve, g = MODES[m_idx]
    wb = WHITE_BALANCE if wb_on else None
    tl.GAMMA_LUT_R, tl.GAMMA_LUT_G, tl.GAMMA_LUT_B = build_rgb_luts(
        curve=curve, white_balance=wb, gamma=g
    )
    for i in range(NUM_PIXELS):
        v = int(255 * (i + 1) / NUM_PIXELS)  # wahrnehmungsgleiche Weiss-Rampe
        pixels[i] = (v, v, v)
    pixels.show()
    print("kurve:", label, "weissabgleich:", "EIN" if wb_on else "AUS")


draw()
while True:
    if btn_a.pressed():
        m_idx = (m_idx + 1) % len(MODES)
        draw()
    if btn_b.pressed():
        wb_on = not wb_on
        draw()
    time.sleep(0.02)
