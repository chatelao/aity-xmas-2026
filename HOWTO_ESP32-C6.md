# How-To: CircuitPython on Seeed Studio XIAO ESP32-C6

This guide explains how to install CircuitPython on the **Seeed Studio XIAO ESP32-C6** using a web-only flasher tool, and how to transfer files to the target using either a web browser (Web Workflow) or a file explorer / IDE.

> **Important Note on ESP32-C6 Hardware:**
> Unlike the RP2040, the ESP32-C6 chip does not have a native USB controller for mass-storage emulation. Therefore, **no `CIRCUITPY` USB disk drive will appear** when plugging the board into your computer. Instead, CircuitPython on the ESP32-C6 is programmed via the serial bootloader and managed via CircuitPython **Web Workflow** (over Wi-Fi or Web Serial).

---

## 1. Install CircuitPython (Web Only)

You do not need to install Python or the command-line `esptool.py` locally on your computer. You can flash the board directly from a web browser using the **Adafruit WebSerial ESPTool**.

### Requirements
- A modern web browser supporting the Web Serial API (Google Chrome, Microsoft Edge, Opera, or Firefox 151+).
- A USB-C data cable connecting the XIAO ESP32-C6 to your computer.

### Step 1.1: Obtain the CircuitPython `.bin` File

1. In your browser, navigate to:
   - [circuitpython.org/board/seeed_xiao_esp32c6/](https://circuitpython.org/board/seeed_xiao_esp32c6/)
2. Choose your preferred language (e.g., English or German) and download the **`.bin`** file.
   *(Note: A pre-downloaded stable binary is also included in this repository at `circuitpython/adafruit-circuitpython-seeed_xiao_esp32c6-de_DE-10.3.1.bin`)*.

### Step 1.2: Put XIAO ESP32-C6 into Bootloader Mode

1. Connect the XIAO ESP32-C6 to your computer via USB-C.
2. Enter the ROM bootloader:
   - Press and hold the **`BOOT`** button.
   - Press and release the **`RESET`** button.
   - Release the **`BOOT`** button.
   *(Alternatively, hold `BOOT` while plugging the board into the USB port).*

### Step 1.3: Flash Firmware using Adafruit WebSerial ESPTool

1. Open the **Adafruit WebSerial ESPTool** in your browser:
   - [https://adafruit.github.io/Adafruit_WebSerial_ESPTool/](https://adafruit.github.io/Adafruit_WebSerial_ESPTool/)
2. Set the baud rate to **460800** (or keep the default 115200) and click **Connect** in the top right.
3. Select the serial port corresponding to your ESP32-C6 (e.g. *USB JTAG/serial debug unit* or *ESP32-C6*) and click **Connect**.
4. *(Recommended)* Click **Erase** to wipe previous flash content cleanly. Wait until it reports "Finished."
5. Under **Programming the ESP Microcontroller**:
   - Next to offset **`0x0`**, click **Choose a file...**.
   - Select the downloaded CircuitPython `.bin` file (e.g., `adafruit-circuitpython-seeed_xiao_esp32c6-...bin`).
   - Ensure the offset box remains set to **`0x0`**.
6. Click **Program**. Wait for the flashing progress bar to reach 100%.
7. Press the **`RESET`** button on the XIAO ESP32-C6 to launch CircuitPython!

---

## 2. Transfer Files to the Target

Because the ESP32-C6 lacks native USB mass-storage, you transfer files using the **CircuitPython Web Workflow** via a web browser or using serial/explorer-based tools.

---

### Option A: Using Web Browser (CircuitPython Web Workflow)

CircuitPython has a built-in web server ("Web Workflow") allowing full file browsing, script editing, and library uploads over local Wi-Fi or Web Serial.

#### Step 2.1: Initial Wi-Fi Setup (`settings.toml`)

To activate Web Workflow over your local network, CircuitPython needs Wi-Fi credentials in a file named `settings.toml`. You can configure this directly from your browser:

1. Open the CircuitPython Web Editor in Chrome / Edge:
   - [https://code.circuitpython.org/](https://code.circuitpython.org/)
2. Click **Connect** and select **Web Serial**.
3. Choose the ESP32-C6 serial port to connect to the board.
4. Click the **Serial** tab to open the REPL. Press Enter or `Ctrl+C` to get the `>>> ` prompt.
5. Create `settings.toml` by pasting the following commands (replace with your Wi-Fi name and password):
   ```python
   f = open('settings.toml', 'w')
   f.write('CIRCUITPY_WIFI_SSID = "Your_WiFi_SSID"\n')
   f.write('CIRCUITPY_WIFI_PASSWORD = "Your_WiFi_Password"\n')
   f.write('CIRCUITPY_WEB_API_PASSWORD = "your-password"\n')
   f.close()
   ```
6. Press the **`RESET`** button on the board (or press `Ctrl+D` in the REPL) to reboot. The serial console will print the connected IP address (and hostname `circuitpython.local`).

#### Step 2.2: Access the Built-in Web Browser File Manager

1. Open any web browser on the same Wi-Fi network and visit:
   - `http://circuitpython.local` (or `http://<your-board-ip>`)
2. Log in by entering the password you defined for `CIRCUITPY_WEB_API_PASSWORD` (leave the username blank).
3. Click **File Browser**:
   - You can view the file structure of the board.
   - Click **Browse...** to upload `code.py` directly to the root.
   - Create a directory named `lib/` and upload `circuitpython/default/lib/neopixel.mpy`.
   - Click **Edit** next to `code.py` to modify and save code directly in the browser.
4. Alternatively, open [https://code.circuitpython.org/](https://code.circuitpython.org/), select **Connect -> WiFi**, and manage your code with full syntax highlighting.

---

### Option B: Using File Explorer / IDE (Thonny, mpremote, or WebDAV)

If you prefer a desktop file tree experience without native USB mass storage:

1. **Using Thonny IDE (File Explorer built-in):**
   - Open **Thonny IDE** (available for Windows, macOS, Linux).
   - Go to **Tools -> Options -> Interpreter** and select **CircuitPython (generic)** and your ESP32-C6 COM port.
   - In Thonny's menu, enable **View -> Files**.
   - You will see two panes: the top pane is your local computer and the bottom pane is **CircuitPython device**.
   - Simply right-click on `code.py` and `lib/` on your computer and select **"Upload to /"** to transfer them directly to the board.
2. **Using WebDAV (Mounting as a Drive):**
   - CircuitPython Web Workflow supports WebDAV (`http://circuitpython.local/fs/` or `http://<ip>/fs/`).
   - On Windows, you can map `http://<board-ip>/fs/` as a Network Drive in Windows Explorer.
   - On macOS, open Finder, click **Go -> Connect to Server**, and enter `http://circuitpython.local/fs/`.
   - On Linux, use your file manager (Nautilus/Dolphin) to connect to `dav://circuitpython.local/fs/`.
   - Authenticate with the `CIRCUITPY_WEB_API_PASSWORD`. The board's filesystem will mount just like a folder in your file explorer!
