# code.test.py
# Hardware-Tester fuer Seeed Studio XIAO RP2040
# Abhaengigkeiten: /lib/neopixel.mpy
#
# Funktion:
# a) Steuert die 60 NeoPixel-LEDs an D10 in 3 Gruppen (jede 3. LED),
#    wechselt alle 700 ms die Gruppe und durchlaeuft dabei:
#    3x Rot, 3x Gruen, 3x Blau, 3x Weiss, dann wieder von vorne.
# b) Zeigt den Status der Taster D5 und D6 auf der eingebauten
#    NeoPixel-LED des XIAO RP2040 an:
#    - Dunkelblau: kein Knopf gedrueckt
#    - Gruen:      nur D5 gedrueckt
#    - Rot:        nur D6 gedrueckt
#    - Weiss:      D5 + D6 gedrueckt

import time
import board
import digitalio
import neopixel

# --- LED-Streifen (60 NeoPixel an D10) ---
NUM_LEDS = 60
STEP_INTERVAL = 0.7  # 700 ms

leds = neopixel.NeoPixel(
    board.D10,
    NUM_LEDS,
    brightness=0.3,
    auto_write=False,
    pixel_order=neopixel.GRB,
)

# --- Eingebaute NeoPixel-LED des XIAO RP2040 ---
onboard_pixel = None
try:
    if hasattr(board, "NEOPIXEL_POWER"):
        np_pwr = digitalio.DigitalInOut(board.NEOPIXEL_POWER)
        np_pwr.direction = digitalio.Direction.OUTPUT
        np_pwr.value = True
    onboard_pixel = neopixel.NeoPixel(
        board.NEOPIXEL,
        1,
        brightness=0.3,
        auto_write=True,
    )
except Exception:
    onboard_pixel = None

# --- Taster an D5 und D6 (aktiv-low gegen GND mit internem Pull-Up) ---
btn_d5 = digitalio.DigitalInOut(board.D5)
btn_d5.switch_to_input(pull=digitalio.Pull.UP)

btn_d6 = digitalio.DigitalInOut(board.D6)
btn_d6.switch_to_input(pull=digitalio.Pull.UP)

# --- Farben ---
STRIP_COLORS = (
    (255, 0, 0),      # Rot
    (0, 255, 0),      # Gruen
    (0, 0, 255),      # Blau
    (255, 255, 255),  # Weiss
)
TOTAL_STEPS = len(STRIP_COLORS) * 3  # 12 Schritte: 3x R, 3x G, 3x B, 3x W

ONBOARD_DARK_BLUE = (0, 0, 30)
ONBOARD_GREEN = (0, 255, 0)
ONBOARD_RED = (255, 0, 0)
ONBOARD_WHITE = (255, 255, 255)


def render_strip(step):
    """Schaltet jede 3. LED der aktuellen Gruppe in der aktuellen Farbe ein."""
    color = STRIP_COLORS[step // 3]
    group = step % 3
    leds.fill((0, 0, 0))
    for i in range(group, NUM_LEDS, 3):
        leds[i] = color
    leds.show()


def get_onboard_color(d5_pressed, d6_pressed):
    """Bestimmt die Statusfarbe fuer die Onboard-NeoPixel-LED."""
    if d5_pressed and d6_pressed:
        return ONBOARD_WHITE
    if d5_pressed:
        return ONBOARD_GREEN
    if d6_pressed:
        return ONBOARD_RED
    return ONBOARD_DARK_BLUE


step = 0
render_strip(step)
last_step_time = time.monotonic()
last_onboard_color = None

while True:
    now = time.monotonic()
    if now - last_step_time >= STEP_INTERVAL:
        last_step_time += STEP_INTERVAL
        if now - last_step_time >= STEP_INTERVAL:
            last_step_time = now
        step = (step + 1) % TOTAL_STEPS
        render_strip(step)

    if onboard_pixel is not None:
        d5_pressed = not btn_d5.value
        d6_pressed = not btn_d6.value
        onboard_color = get_onboard_color(d5_pressed, d6_pressed)
        if onboard_color != last_onboard_color:
            onboard_pixel[0] = onboard_color
            last_onboard_color = onboard_color

    time.sleep(0.02)
