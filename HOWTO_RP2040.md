# How-To: CircuitPython on Seeed Studio XIAO RP2040

This guide explains how to install CircuitPython on the **Seeed Studio XIAO RP2040** (web-only method) and how to transfer files to the target using either a web browser or your system's file explorer.

---

## 1. Install CircuitPython (Web Only)

The Seeed Studio XIAO RP2040 features native USB support with the Raspberry Pi RP2040 ROM bootloader (UF2). You do not need any local CLI tools or Python installations—flashing is done entirely through your web browser and the built-in USB bootloader.

### Step 1.1: Enter Bootloader Mode

1. Connect the XIAO RP2040 to your computer using a USB-C data cable.
2. Put the board into bootloader mode using either of these methods:
   - Hold down the small **`B` (BOOT)** button on the board, press and release the **`R` (RESET)** button, then release `BOOT`.
   - Alternatively, unplug the USB cable, hold down the **`B` (BOOT)** button while plugging the USB cable into your computer, then release `BOOT`.
3. A mass storage drive named **`RPI-RP2`** will appear in your operating system.

### Step 1.2: Download CircuitPython Firmware via Browser

1. In your web browser, navigate to the official CircuitPython board page for the XIAO RP2040:
   - [circuitpython.org/board/seeeduino_xiao_rp2040/](https://circuitpython.org/board/seeeduino_xiao_rp2040/)
2. Choose your preferred language (e.g., English or German) and click **DOWNLOAD .UF2 NOW**.
   *(Note: A pre-downloaded stable UF2 firmware binary is also included in this repository at `circuitpython/adafruit-circuitpython-seeeduino_xiao_rp2040-de_DE-10.3.1.uf2`)*.
3. Save the `.uf2` file to your computer.

### Step 1.3: Flash CircuitPython to the Target

1. Drag and drop (or copy) the downloaded `.uf2` file directly onto the **`RPI-RP2`** drive.
2. The board will automatically flash the firmware, unmount `RPI-RP2`, and reboot.
3. Once rebooted, a new removable drive named **`CIRCUITPY`** will appear. CircuitPython is now successfully installed!

---

## 2. Transfer Files to the Target

You can manage, upload, and edit scripts (`code.py`) and libraries on the XIAO RP2040 using either your system's File Explorer or completely within a Web Browser.

### Option A: Using File Explorer (Drag & Drop)

Because the RP2040 has native USB support, the XIAO RP2040 mounts as a standard USB mass-storage drive named **`CIRCUITPY`**.

1. Open **File Explorer** (Windows), **Finder** (macOS), or your Linux file manager.
2. Navigate to the **`CIRCUITPY`** drive.
3. **Upload the code:**
   - Copy `circuitpython/default/code.py` (or your customized script) directly to the root of the `CIRCUITPY` drive as `code.py`.
4. **Upload required libraries:**
   - On the `CIRCUITPY` drive, create a folder named `lib` if it does not already exist.
   - Copy `neopixel.mpy` (located in `circuitpython/default/lib/`) into the `CIRCUITPY/lib/` folder.
5. As soon as you save or copy `code.py`, CircuitPython automatically restarts and runs the script!

---

### Option B: Using Web Browser (Web Editor / Web Serial)

If you prefer coding and managing files entirely in your browser without desktop tools:

1. Open a Chromium-based browser (Google Chrome, Microsoft Edge, Opera, or Firefox 151+).
2. Navigate to the CircuitPython Web Editor:
   - [https://code.circuitpython.org/](https://code.circuitpython.org/)
3. Click **Connect** in the top-left corner:
   - Select **USB** / **Select USB Host Folder** (or Web Serial if available).
   - When prompted by the browser, select the **`CIRCUITPY`** root folder and grant read/write permissions.
4. Once connected:
   - You can view and edit `code.py` directly in the browser editor.
   - Click **Save + Run** to immediately save the script to the board and restart execution.
   - Use the **Upload Files** or **Upload Folders** buttons to upload `lib/neopixel.mpy` or other assets directly onto the board.
   - Click the **Serial** tab to view live serial prints and access the interactive REPL.
