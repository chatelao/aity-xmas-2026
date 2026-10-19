# AITY Xmas Tree 2026

An interactive Christmas tree PCB powered by a Seeed Studio XIAO ESP32-C6 microcontroller, featuring 60 addressable NeoPixel LEDs, a piezo speaker/buzzer, and test point outputs.

## Hardware Specifications

- **Microcontroller:** Seeed Studio XIAO ESP32-C6
- **LEDs:** 60 x WS2812B NeoPixel RGB LEDs connected to pin `D10`
- **Audio:** Speaker/Buzzer connected to pin `D0`
- **Test Points:** TP101 – TP109 connected to pins `D1` – `D9`

## ASCII Pinout Diagram

```
                       +-------------------+
                       |   USB-C           |
                       |  [ Seeed XIAO ]   |
                       |  [ ESP32-C6   ]   |
(Speaker LS101) D0/A0 -| [1]          [14] |- 5V (VDD Power)
 (TestPoint 1)  D1/A1 -| [2]          [13] |- GND
 (TestPoint 3)  D2/A2 -| [3]          [12] |- 3V3 (NC)
 (TestPoint 4)  D3/A3 -| [4]          [11] |- D10/MOSI (60 x NeoPixel LEDs)
 (TestPoint 5) D4/SDA -| [5]          [10] |- D9/MISO  (TestPoint 2)
 (TestPoint 8) D5/SCL -| [6]           [9] |- D8/SCK   (TestPoint 7)
 (TestPoint 6)  D6/TX -| [7]           [8] |- D7/RX    (TestPoint 9)
                       +-------------------+
```

### Pin Mapping Table

| Pin Number | XIAO Pin Name | CircuitPython Pin | Connection / Function |
|------------|---------------|-------------------|-----------------------|
| 1          | PA02_A0_D0    | `board.D0`        | Speaker (LS101)       |
| 2          | PA4_A1_D1     | `board.D1`        | TestPoint 1 (TP101)   |
| 3          | PA10_A2_D2    | `board.D2`        | TestPoint 3 (TP103)   |
| 4          | PA11_A3_D3    | `board.D3`        | TestPoint 4 (TP104)   |
| 5          | PA8_A4_D4_SDA | `board.D4`        | TestPoint 5 (TP105)   |
| 6          | PA9_A5_D5_SCL | `board.D5`        | TestPoint 8 (TP108)   |
| 7          | PB08_A6_D6_TX | `board.D6`        | TestPoint 6 (TP106)   |
| 8          | PB09_A7_D7_RX | `board.D7`        | TestPoint 9 (TP109)   |
| 9          | PA7_A8_D8_SCK | `board.D8`        | TestPoint 7 (TP107)   |
| 10         | PA5_A9_D9_MISO| `board.D9`        | TestPoint 2 (TP102)   |
| 11         | PA6_A10_D10   | `board.D10`       | NeoPixel LEDs Data In |
| 12         | 3V3           | `board.3V3`       | Unconnected (NC)      |
| 13         | GND           | `board.GND`       | Ground                |
| 14         | 5V            | `board.5V`        | 5V Power (VDD)        |

---

## Example CircuitPython Script: Rainbow Animation

Save the following script as `code.py` or `main.py` on the `CIRCUITPY` drive. Make sure the Adafruit `neopixel` library (`neopixel.mpy`) is placed in the `lib/` folder on your `CIRCUITPY` drive.

```python
import time
import board
import neopixel

# Try importing built-in colorwheel from rainbowio, fallback if not present
try:
    from rainbowio import colorwheel
except ImportError:
    def colorwheel(pos):
        """Generate rainbow colors across 0-255 positions."""
        pos = int(pos) % 256
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)

# Configuration
NUM_LEDS = 60
DATA_PIN = board.D10
BRIGHTNESS = 0.3  # Adjust brightness (0.0 to 1.0)

# Initialize NeoPixel strip
pixels = neopixel.NeoPixel(
    DATA_PIN,
    NUM_LEDS,
    brightness=BRIGHTNESS,
    auto_write=False
)

def rainbow_cycle(wait=0.01):
    """Animate a smooth moving rainbow across all 60 LEDs."""
    for j in range(256):
        for i in range(NUM_LEDS):
            pixel_index = (i * 256 // NUM_LEDS) + j
            pixels[i] = colorwheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

print("Starting Rainbow Animation on 60 NeoPixel LEDs...")

while True:
    rainbow_cycle(wait=0.01)
```

## Setup Instructions

1. Install CircuitPython on your Seeed Studio XIAO ESP32-C6.
2. Download the Adafruit CircuitPython Library Bundle.
3. Copy `neopixel.mpy` (and `rainbowio` if using external bundle) into the `lib/` folder on your `CIRCUITPY` drive.
4. Save the example script above as `code.py` on your `CIRCUITPY` drive.
