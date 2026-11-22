# AITY Weihnachtsbaum 2026 — ESP32-C6 Zero-Install Captive Portal Firmware

Eigenständige ESP-IDF-Firmware für den **Seeed Studio XIAO ESP32-C6** auf dem **AITY Weihnachtsbaum 2026** PCB.  
Sie bietet **100 % Funktionsparität** zu [`chatelao/android-xmas-tree-app`](https://github.com/chatelao/android-xmas-tree-app) ganz ohne App-Installation: Einfach mit dem Smartphone, Tablet oder Laptop in das WLAN des Baums einwählen und die Steuerungsoberfläche öffnet sich automatisch per Captive-Portal-Weiterleitung.

## Zero-Install-Ablauf

1. Den AITY Weihnachtsbaum per USB-C mit Strom versorgen.
2. Auf dem Smartphone oder Computer mit dem offenen WLAN **`AITY-Xmas-Tree`** verbinden (kein Passwort nötig).
3. Das Betriebssystem erkennt das Captive Portal automatisch und öffnet **`http://192.168.4.1/`** (funktioniert unter Android, iOS, macOS, Windows und Linux).
4. Alle 60 NeoPixel-LEDs, festliche Melodien, den Farbkreis und gespeicherte Presets direkt im Browser steuern — 100 % offline, ohne externe Abhängigkeiten.

## Funktionen (Volle Parität zu `android-xmas-tree-app`)

- **13 Leuchtmuster (`0..12`)**:
  - `Aus`, `Statisch`, `Regenbogen`, `Funkeln`, `Kerzenschein`, `Twinkle`, `Lauflicht`, `Segmente` (Auto-Zyklus + 6 virtuelle Baum-Segmente inkl. Stern Innen/Außen), `Schockwelle` (4 PCB-Zentren: Stern, Stiel, Baummitte, Basis), `Plasma` (2D-Interferenz), `Polar-Wirbel`, `Gravitations-Puls` und `TwinkleFOX` (10 Weihnachtspaletten mit warmweißem Fairy-Light-Stern).
- **Interaktiver Farbkreis & Helligkeit**:
  - Touch-/Maus-RGB-Farbkreis, 5 Schnellauswahl-Farben, Helligkeitsregler (`0–100 %`), Geschwindigkeitsregler (`1–100 %`) sowie Live-Vorschau der 60 LEDs.
- **Festliche Melodien (RTTTL über LEDC PWM)**:
  - `Stille`, `Jingle Bells`, `We Wish You a Merry Christmas`, `Stille Nacht`, `Deck the Halls`.
  - Abspielen / Pause / Stopp, Lautstärke (`0–100 %`), Tempo (`50–200 %`) und Lautsprecher-Testtöne (`C5`, `E5`, `G5`, `C6`).
- **Preset-Verwaltung direkt auf dem MCU (NVS Flash)**:
  - Vorbelegt mit `Klassische Weihnachten`, `Regenbogen-Party` und `Gemütliche Stille Nacht`.
  - Bis zu 16 eigene Presets im ESP32-C6 Flash speichern, anwenden und löschen — geteilt zwischen allen verbundenen Geräten.
- **Live-Telemetrie & Zustandsspeicherung**:
  - Laufzeit, aktives Muster/Melodie, verbundene Clients, Fehlerstatus und automatische Wiederherstellung beim Neustart.

## Hardware-Pinbelegung (Seeed Studio XIAO ESP32-C6)

Definiert in [`main/include/board_config.h`](main/include/board_config.h):

| Funktion | XIAO-Pin | ESP32-C6 GPIO | Peripherie |
| :--- | :---: | :---: | :--- |
| **60 × WS2812B NeoPixels** | `D10` / `MOSI` | `GPIO 18` | RMT TX-Kanal (10 MHz, nicht-blockierend) |
| **Lautsprecher / Piezo-Buzzer** | `D0` / `A0` | `GPIO 0` | LEDC Low-Speed PWM (10-Bit) |
| **RF-Schalter Stromversorgung** | Intern | `GPIO 3` | Ausgang `LOW` (aktiviert XIAO RF-Schalter) |
| **RF-Antennenauswahl** | Intern | `GPIO 14` | Ausgang `LOW` (interne Keramikantenne) |
| **Verbindungs-Status-LED** | User-LED | `GPIO 15` | Active-LOW (leuchtet bei aktivem Client) |

## Captive Portal & REST-API

- **SoftAP:** SSID `AITY-Xmas-Tree`, Gateway/IP `192.168.4.1/24`.
- **Wildcard-DNS-Server (UDP/53):** Beantwortet alle `A`-Anfragen mit `192.168.4.1` (TTL 60 s) und `AAAA`/`HTTPS`/`SVCB`-Anfragen mit `NOERROR` (0 Antworten) für sofortiges OS-Captive-Portal-Popup.
- **HTTP-Weiterleitungen (TCP/80):** Leitet Captive-Portal-Probes (`/generate_204`, `/gen_204`, `/hotspot-detect.html`, `/library/test/success.html`, `/connecttest.txt`, `/ncsi.txt`, `/redirect`, `/fwlink`, `/canonical.html`, `/success.txt`, `/mobile/status.php`), fremde `Host`-Header und 404-Pfade per `302 Found` auf `http://192.168.4.1/` um.
- **REST-Endpunkte:**
  - `GET /` — Liefert die komprimierte Web-UI (`8,5 KB` gzip).
  - `GET /api/status` — JSON-Telemetrie & aktueller LED-/Audio-Status.
  - `POST /api/lighting` — Muster, Palette/Untermodus, RGB, Helligkeit, Geschwindigkeit aktualisieren (NVS-gespeichert).
  - `POST /api/audio` — Melodie, Wiedergabe-Status, Lautstärke, Tempo oder Testton (`freq_hz`, `duration_ms`) steuern.
  - `GET /api/presets` — Gespeicherte Presets aus dem NVS abrufen.
  - `POST /api/presets` — Neues Preset im NVS speichern.
  - `POST /api/presets/apply` — Preset per `id` anwenden.
  - `POST /api/presets/delete` — Preset per `id` löschen.

## Bauen & Flashen

### Option 1: Vorkompilierte Binary im Browser flashen (ohne Toolchain)
`XmasTreePortal_xiao_esp32c6.bin` aus den GitHub Releases laden und bei Offset **`0x0`** mit dem [Adafruit WebSerial ESPTool](https://adafruit.github.io/Adafruit_WebSerial_ESPTool/) flashen.

### Option 2: Lokal mit ESP-IDF (v5.3+) bauen
```bash
cd esp32c6-portal
# Nach Änderungen an web_ui/index.html Header neu generieren:
python3 scripts/embed_web_ui.py

idf.py set-target esp32c6
idf.py build
idf.py -p /dev/ttyACM0 flash monitor
```

## Tests ausführen

```bash
# Host-C-Unit-Tests (LED-Engine, RTTTL-Audio, NVS, Presets, DNS, HTTP-API)
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

# Eingebettete Web-UI & Gzip-Header prüfen
node esp32c6-portal/test/test_web_ui.mjs
```
