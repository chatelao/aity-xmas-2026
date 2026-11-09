import time
import board
import digitalio
import neopixel

# --- 1. Initialize NeoPixel Strip on D10 AND Onboard RGB LED ---
NUM_LEDS = 60
leds = neopixel.NeoPixel(board.D10, NUM_LEDS, brightness=0.5, auto_write=False, pixel_order=neopixel.GRB)

# XIAO RP2040 has a built-in NeoPixel on board.NEOPIXEL (powered viaNEOPIXEL_POWER)
try:
    np_pwr = digitalio.DigitalInOut(board.NEOPIXEL_POWER)
    np_pwr.direction = digitalio.Direction.OUTPUT
    np_pwr.value = True
    onboard_pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.3)
except Exception:
    onboard_pixel = None

# --- 2. Scan ALL candidate pins (in case D5/D6 vs GPIO5/GPIO6 were mixed up) ---
# XIAO RP2040 Silkscreen -> RP2040 GPIO mapping:
# D0=GP26, D1=GP27, D2=GP28, D3=GP29, D4=GP6, D5=GP7, D6=GP0, D7=GP1, D8=GP2, D9=GP4
CANDIDATE_PINS = [
    ("D0", board.D0), ("D1", board.D1), ("D2", board.D2),
    ("D3", board.D3), ("D4", board.D4), ("D5", board.D5),
    ("D6", board.D6), ("D7", board.D7), ("D8", board.D8),
    ("D9", board.D9)
]

inputs = {}
for name, pin in CANDIDATE_PINS:
    dio = digitalio.DigitalInOut(pin)
    dio.direction = digitalio.Direction.INPUT
    dio.pull = digitalio.Pull.UP
    inputs[name] = dio

print("=== XIAO RP2040 PIN SCANNER STARTED ===")
print("Idle state should have NO pins grounded. Touch a wire from GND to D5 or D6.")

last_print = 0.0

while True:
    # Check which pins are currently pulled LOW (False) to GND
    grounded_pins = [name for name, dio in inputs.items() if not dio.value]

    # Base Idle Pattern: First 3 LEDs dim white so you KNOW the LED strip is working!
    leds.fill((0, 0, 0))
    leds[0] = (15, 15, 15)
    leds[1] = (15, 15, 15)
    leds[2] = (15, 15, 15)

    # Check D6 (1st LED Green) and D5 (10th LED Red) directly by voltage level
    if "D6" in grounded_pins:
        leds[0] = (0, 255, 0)   # Physical LED 1 -> Bright Green
        leds[1] = (0, 0, 80)    # Physical LED 2 -> Blue

    if "D5" in grounded_pins:
        leds[9] = (255, 0, 0)   # Physical LED 10 -> Bright Red
        leds[10] = (80, 80, 0)  # Physical LED 11 -> Yellow

    # If ANY OTHER pin (e.g. D4/GPIO6) is grounded by mistake, light LED 5 Purple!
    other_pins = [p for p in grounded_pins if p not in ("D5", "D6")]
    if other_pins:
        leds[4] = (200, 0, 200) # Physical LED 5 -> Purple (Wrong pin wired!)

    leds.show()

    # Mirror status on the XIAO's built-in RGB LED (works even if strip wiring is broken)
    if onboard_pixel:
        if "D6" in grounded_pins:
            onboard_pixel[0] = (0, 255, 0)   # Green for D6
        elif "D5" in grounded_pins:
            onboard_pixel[0] = (255, 0, 0)   # Red for D5
        elif other_pins:
            onboard_pixel[0] = (200, 0, 200) # Purple for D0-D4 / D7-D9
        else:
            onboard_pixel[0] = (0, 0, 20)    # Dim Blue = Idle & Running

    # Print status every 0.25s to Serial Console
    now = time.monotonic()
    if now - last_print >= 0.25:
        last_print = now
        print(f"Grounded pins right now: {grounded_pins if grounded_pins else 'NONE (All HIGH 3.3V)'}")

    time.sleep(0.02)

