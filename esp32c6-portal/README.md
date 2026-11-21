# AITY Xmas Tree 2026 — ESP32-C6 Zero-Install Captive Portal Firmware

Standalone ESP-IDF firmware for the **Seeed Studio XIAO ESP32-C6** on the **AITY Xmas Tree 2026** PCB.  
It provides **100% feature parity** with [`chatelao/android-xmas-tree-app`](https://github.com/chatelao/android-xmas-tree-app) without installing any mobile app: simply connect any phone, tablet, or laptop to the tree's Wi-Fi Access Point and the control webpage opens automatically via Captive Portal redirect.

## Zero-Install User Flow

1. Power on the AITY Xmas Tree (USB-C).
2. On any smartphone or computer, connect to the open Wi-Fi network **`AITY-Xmas-Tree`** (no password required).
3. Your device automatically detects the Captive Portal and opens **`http://192.168.4.1/`** (works on Android, iOS, macOS, Windows, and Linux).
4. Control all 60 NeoPixel LEDs, festive melodies, custom color wheel, and saved presets directly from the embedded webpage — 100% offline, zero external dependencies.

## Features (Full Parity with `android-xmas-tree-app`)

- **13 Lighting Patterns (`0..12`)**:
  - `Off`, `Static`, `Rainbow`, `Sparkle`, `Candle`, `Twinkle`, `Lauflicht` (Comet Chase), `Segments` (Auto Cycle + 6 virtual tree segments including Star Inner/Outer), `Shockwave` (4 PCB epicenters: Star, Stem, Tree Center, Base), `Plasma` (2D interference), `Polar Vortex`, `Gravity Pulse`, and `TwinkleFOX` (10 festive palettes with warm-gold Fairy Light star).
- **Interactive Color Wheel & Intensity**:
  - Touch/mouse RGB color wheel, 5 quick festive swatches, brightness slider (`0–100%`), animation speed slider (`1–100%`), and a live 60-LED tree preview canvas.
- **Festive Melody Player (RTTTL over LEDC PWM)**:
  - `Silent`, `Jingle Bells`, `We Wish You a Merry Christmas`, `Silent Night`, `Deck the Halls`.
  - Play / Pause / Stop transport, volume (`0–100%`), tempo (`50–200%`), and one-tap speaker tone test buttons (`C5`, `E5`, `G5`, `C6`).
- **On-MCU Preset Manager (NVS Flash)**:
  - Pre-loaded with `Classic Christmas`, `Rainbow Party`, and `Cozy Silent Night`.
  - Save, apply, and delete up to 16 custom presets directly on the ESP32-C6 flash so every connected device shares the same presets.
- **Live Telemetry & State Persistence**:
  - Real-time uptime, active mode, connected client count, error status, and automatic NVS state restore on reboot.

## Hardware Pinout (Seeed Studio XIAO ESP32-C6)

Defined in [`main/include/board_config.h`](main/include/board_config.h):

| Function | XIAO Pin | ESP32-C6 GPIO | Peripheral |
| :--- | :---: | :---: | :--- |
| **60 × WS2812B NeoPixels** | `D10` / `MOSI` | `GPIO 18` | RMT TX Channel (10 MHz, non-blocking) |
| **Speaker / Piezo Buzzer** | `D0` / `A0` | `GPIO 0` | LEDC Low-Speed PWM (10-bit) |
| **RF Switch Power Enable** | Internal | `GPIO 3` | Output `LOW` (enables XIAO RF switch) |
| **RF Antenna Select** | Internal | `GPIO 14` | Output `LOW` (onboard ceramic antenna) |
| **Connection Status LED** | User LED | `GPIO 15` | Active-LOW (ON when client connected) |

## Captive Portal & REST API

- **SoftAP:** SSID `AITY-Xmas-Tree`, Gateway/IP `192.168.4.1/24`.
- **Wildcard DNS Server (UDP/53):** Answers all `A` queries with `192.168.4.1` (TTL 60s) and responds cleanly with `NOERROR` (0 answers) to `AAAA`/`HTTPS`/`SVCB` queries for instant OS captive-portal popup.
- **Captive Portal HTTP Redirects (TCP/80):** Redirects `/generate_204`, `/gen_204`, `/hotspot-detect.html`, `/library/test/success.html`, `/connecttest.txt`, `/ncsi.txt`, `/redirect`, `/fwlink`, `/canonical.html`, `/success.txt`, `/mobile/status.php`, foreign `Host` headers, and 404 paths via `302 Found` to `http://192.168.4.1/`.
- **REST Endpoints:**
  - `GET /` — Serves the gzipped self-contained Web UI (`8.5 KB`).
  - `GET /api/status` — Returns JSON telemetry & current LED/audio state.
  - `POST /api/lighting` — Updates pattern, palette/sub-mode, RGB, brightness, speed (persists to NVS).
  - `POST /api/audio` — Updates melody, playback state, volume, tempo, or plays a one-shot test tone (`freq_hz`, `duration_ms`).
  - `GET /api/presets` — Lists saved presets from NVS.
  - `POST /api/presets` — Saves a new preset to NVS.
  - `POST /api/presets/apply` — Applies a preset by `id` (lighting + audio).
  - `POST /api/presets/delete` — Deletes a preset by `id`.

## Building & Flashing

### Option 1: Flash Pre-Built Binary in Browser (Zero Toolchain)
Download `XmasTreePortal_xiao_esp32c6.bin` from GitHub Releases (or the `Build ESP32-C6 Captive Portal Firmware` Actions artifact) and flash at offset **`0x0`** using [Adafruit WebSerial ESPTool](https://adafruit.github.io/Adafruit_WebSerial_ESPTool/).

### Option 2: Build Locally with ESP-IDF (v5.3+)
```bash
cd esp32c6-portal
# If you edit web_ui/index.html, regenerate main/include/web_ui_gz.h:
python3 scripts/embed_web_ui.py

idf.py set-target esp32c6
idf.py build
idf.py -p /dev/ttyACM0 flash monitor
```

## Running Unit & Web UI Tests

```bash
# Host C unit tests (LED engine, RTTTL audio, NVS, presets, DNS, HTTP API)
gcc -std=c11 -Wall -Wextra -Werror -Iesp32c6-portal/main/include \
  esp32c6-portal/main/src/led_engine.c \
  esp32c6-portal/main/src/audio_engine.c \
  esp32c6-portal/main/src/nvs_manager.c \
  esp32c6-portal/main/src/preset_store.c \
  esp32c6-portal/main/src/dns_server.c \
  esp32c6-portal/main/src/http_server.c \
  esp32c6-portal/main/src/wifi_ap.c \
  esp32c6-portal/test/test_firmware.c \
  -lm -o /tmp/test_esp32c6_portal && /tmp/test_esp32c6_portal

# Self-contained Web UI & gzip header sync verification
node esp32c6-portal/test/test_web_ui.mjs
```
---

## License

Licensed under **Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC-4.0)**. See [`LICENSE`](../LICENSE) or <https://creativecommons.org/licenses/by-nc/4.0/>.
