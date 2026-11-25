# CircuitPython

Firmware binaries, example scripts, and helper libraries for the 60-LED Xmas tree PCB, compatible with the **Seeed Studio XIAO RP2040** and **XIAO ESP32-C6**.

For flashing and file-transfer instructions, see [HOWTO_RP2040.md](../HOWTO_RP2040.md) and [HOWTO_ESP32-C6.md](../HOWTO_ESP32-C6.md).

## Contents

### Firmware

| File | Target Board | Version |
|------|--------------|---------|
| `adafruit-circuitpython-seeeduino_xiao_rp2040-de_DE-10.3.1.uf2` | Seeed Studio XIAO RP2040 | 10.3.1 (`de_DE`) |
| `adafruit-circuitpython-seeed_xiao_esp32c6-de_DE-10.3.1.bin` | Seeed Studio XIAO ESP32-C6 | 10.3.1 (`de_DE`) |

### Default Bundle (`default/`)

| Path | Description |
|------|-------------|
| [`default/code.py`](default/code.py) | Diagnostic pin scanner & LED test (checks `D0`–`D9` for GND contact, lights LEDs and prints to serial) |
| [`default/lib/neopixel.mpy`](default/lib/neopixel.mpy) | Pre-packaged Adafruit `neopixel` library required by all LED scripts |

### Example Scripts

All example scripts drive the 60 NeoPixels on `board.D10` and use buttons on `board.D5` and `board.D6` (active-low with internal pull-up). Copy any script to the `CIRCUITPY` drive as `code.py` and make sure `neopixel.mpy` is in `CIRCUITPY/lib/`.

| Script | Description | `D5` | `D6` |
|--------|-------------|------|------|
| [`code.1-sechs-LED.py`](code.1-sechs-LED.py) | Static primary/secondary colors on the first 3 or 6 LEDs | Toggle 3 / 6 LEDs | Blank LEDs while held |
| [`code.2-lauflicht.py`](code.2-lauflicht.py) | Non-blocking chasing light with fading trail | Reverse direction | Cycle speed |
| [`code.3-segmente.py`](code.3-segmente.py) | Highlights each of the 6 tree segments (star, boughs, stem) | Toggle auto / manual | Next segment |
| [`code.4-koordinaten.py`](code.4-koordinaten.py) | Radial wave explosions from 3 epicenters using KiCad coordinates | Retrigger wave | Next epicenter |
| [`code.5-maximal.py`](code.5-maximal.py) | 2D plasma, polar vortex, and gravity pulse with gamma correction | Switch mode | Shift palette |
| [`code.7-twinkle.py`](code.7-twinkle.py) | Full-tree TwinkleFOX animation with 10 palettes & warm-gold star | Next palette | Cycle speed |
| [`code.unified.py`](code.unified.py) | Unified firmware combining all 8 modes (TwinkleFOX, Sechs LEDs, Lauflicht, Segmente, Koordinaten, Plasma, Vortex, Gravity) | Tap: Prev mode · Hold: Prev palette · 2×Tap: Slower | Tap: Next mode · Hold: Next palette · 2×Tap: Faster |
| [`code.test.py`](code.test.py) | Hardware tester (XIAO RP2040): every 3rd LED cycles every 700 ms (3×R, 3×G, 3×B, 3×W) + onboard NeoPixel status for buttons | Onboard Green (White with D6) | Onboard Red (White with D5) |
| [`code.portal.py`](code.portal.py) | **Zero-Install Wi-Fi Captive Portal** for **XIAO ESP32-C6** (`192.168.4.1` AP + DNS/HTTP redirect + [`web_ui.html.gz`](web_ui.html.gz), 100% parity with `android-xmas-tree-app`) | — | — |

### Libraries (`lib/`)

Reusable modules for geometry/segments ([`tannenbaum_layout.py`](lib/tannenbaum_layout.py)) and TwinkleFOX-style palettes and effects ([`tannenbaum_palettes.py`](lib/tannenbaum_palettes.py)). See [`lib/README.md`](lib/README.md) for full documentation and examples.
---

## License

Licensed under **Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC-4.0)**. See [`LICENSE`](../LICENSE) or <https://creativecommons.org/licenses/by-nc/4.0/>.
