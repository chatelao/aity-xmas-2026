# AITY Xmas Tree 2026

An interactive Christmas tree PCB designed to work with either a **Seeed Studio XIAO RP2040** or a **Seeed Studio XIAO ESP32-C6** microcontroller module, featuring 60 addressable NeoPixel LEDs, a piezo speaker/buzzer, and test point outputs.

## Hardware Specifications

- **Microcontroller:** Seeed Studio XIAO RP2040 or Seeed Studio XIAO ESP32-C6
- **LEDs:** 60 x WS2812B NeoPixel RGB LEDs connected to pin `D10`
- **Audio:** Speaker/Buzzer connected to pin `D0`
- **Test Points:** TP101 – TP109 connected to pins `D1` – `D9`

## ASCII Pinout Diagram

Both XIAO boards share the same standard XIAO form factor and 14-pin pinout:

```
                       +-------------------+
                       |   USB-C           |
                       |  [ Seeed XIAO ]   |
                       | [RP2040/ESP32-C6] |
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

| Pin Number | XIAO Pin Name | RP2040 GPIO | ESP32-C6 GPIO | CircuitPython Pin | Connection / Function |
|------------|---------------|-------------|---------------|-------------------|-----------------------|
| 1          | A0 / D0       | GPIO26      | GPIO0 / PA02  | `board.D0`        | Speaker (LS101)       |
| 2          | A1 / D1       | GPIO27      | GPIO1 / PA04  | `board.D1`        | TestPoint 1 (TP101)   |
| 3          | A2 / D2       | GPIO28      | GPIO2 / PA10  | `board.D2`        | TestPoint 3 (TP103)   |
| 4          | A3 / D3       | GPIO29      | GPIO3 / PA11  | `board.D3`        | TestPoint 4 (TP104)   |
| 5          | SDA / D4      | GPIO6       | GPIO19 / PA08 | `board.D4`        | TestPoint 5 (TP105)   |
| 6          | SCL / D5      | GPIO7       | GPIO20 / PA09 | `board.D5`        | TestPoint 8 (TP108)   |
| 7          | TX / D6       | GPIO0       | GPIO21 / PB08 | `board.D6`        | TestPoint 6 (TP106)   |
| 8          | RX / D7       | GPIO1       | GPIO22 / PB09 | `board.D7`        | TestPoint 9 (TP109)   |
| 9          | SCK / D8      | GPIO2       | GPIO23 / PA07 | `board.D8`        | TestPoint 7 (TP107)   |
| 10         | MISO / D9     | GPIO4       | GPIO9 / PA05  | `board.D9`        | TestPoint 2 (TP102)   |
| 11         | MOSI / D10    | GPIO3       | GPIO18 / PA06 | `board.D10`       | NeoPixel LEDs Data In |
| 12         | 3V3           | 3V3         | 3V3           | `board.3V3`       | Unconnected (NC)      |
| 13         | GND           | GND         | GND           | `board.GND`       | Ground                |
| 14         | 5V            | 5V          | 5V            | `board.5V`        | 5V Power (VDD)        |

---

## Platform Setup & Installation Guides

Detailed instructions on how to install CircuitPython (web-only method) and transfer files (via web browser or file explorer) for each platform:

- [**HOWTO_RP2040.md**](HOWTO_RP2040.md) — Guide for **Seeed Studio XIAO RP2040**
- [**HOWTO_ESP32-C6.md**](HOWTO_ESP32-C6.md) — Guide for **Seeed Studio XIAO ESP32-C6**

---

## Example CircuitPython Script: Rainbow Animation

Save the following script as `code.py` or `main.py` on the target device. Make sure the Adafruit `neopixel` library (`neopixel.mpy`) is placed in the `lib/` folder.

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

1. Install CircuitPython on your board (see [HOWTO_RP2040.md](HOWTO_RP2040.md) for XIAO RP2040 or [HOWTO_ESP32-C6.md](HOWTO_ESP32-C6.md) for XIAO ESP32-C6).
2. Obtain the Adafruit CircuitPython Library Bundle (or use the pre-packaged files in `circuitpython/default/`).
3. Copy `neopixel.mpy` into the `lib/` directory on the target board (using file explorer for RP2040 or web workflow for ESP32-C6).
4. Save the example script above (or `circuitpython/default/code.py`) as `code.py` on the target board.
