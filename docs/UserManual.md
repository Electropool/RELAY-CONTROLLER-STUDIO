# Relay Controller Studio - User Manual

Welcome to **Relay Controller Studio**, the complete graphical tool for configuring and flashing multi-channel industrial relay timing systems onto Arduino and ESP32 hardware without needing Python, the Arduino IDE, or technical programming knowledge.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Supported Hardware](#2-supported-hardware)
3. [First Startup Wizard & Installation](#3-first-startup-wizard--installation)
4. [User Interface Overview](#4-user-interface-overview)
5. [Configuring Relay Timings](#5-configuring-relay-timings)
6. [Project File Management & Crash Recovery](#6-project-file-management--crash-recovery)
7. [Firmware Compilation & Flashing](#7-firmware-compilation--flashing)
8. [Troubleshooting & Driver Installation](#8-troubleshooting--driver-installation)

---

## 1. Overview

Relay Controller Studio provides an all-in-one desktop environment to:
- Define loop cycle times and start/stop schedules for relay channels (2CH, 4CH, 8CH, 16CH).
- Configure display settings (brightness, active-low/high polarity, countdown display).
- Validate configurations in real-time to prevent timing conflicts or invalid ranges.
- Automatically compile C++ firmware via an embedded portable Arduino CLI toolchain.
- Flash firmware directly to connected microcontrollers with automatic port and board detection.

---

## 2. Supported Hardware

### Microcontrollers
- **Arduino UNO** (ATmega328P)
- **Arduino Nano** (ATmega328P - New & Old Bootloader variants supported automatically)
- **ESP32** (ESP32-WROOM / DevKit v1)

### Peripherals
- **Relay Modules**: 2-channel, 4-channel, 8-channel, and 16-channel active-LOW or active-HIGH relay boards.
- **Display**: 4-Digit 7-Segment TM1637 Display module for countdown visualization.

---

## 3. First Startup Wizard & Installation

### Portable Standalone Executable
Relay Controller Studio is distributed as a standalone Windows executable (`RelayControllerStudio_Release.exe`). It requires no installation of Python or Arduino IDE.

### Startup Wizard
On your first launch:
1. The **First Startup Wizard** automatically checks for the local `arduino-cli` binary.
2. If missing, it downloads a portable copy directly into the `tools/` folder.
3. It installs required core packages (`arduino:avr`, `esp32:esp32`) and libraries (`TM1637`).
4. Once completed, click **Finish & Launch** to open the main studio interface.

---

## 4. User Interface Overview

The main application window is organized into 5 primary regions:

1. **Board Selection Panel**: Select board type (Arduino UNO/Nano or ESP32), auto-detect connected USB ports, and initiate flashing.
2. **Firmware Configuration Panel**: Select channel count (2CH, 4CH, 8CH, 16CH), set global loop cycle time (seconds), active-low polarity, TM1637 display brightness, and countdown toggle.
3. **Validation Summary Panel**: Displays active warnings or errors if any timing configuration violates physical or logical rules.
4. **Relay Schedule Table**: Interactive table to enable/disable channels and set start/stop times in seconds.
5. **Console & Progress Bar**: Real-time compiler and upload logs, streaming `arduino-cli` output line-by-line during compilation and flashing.

---

## 5. Configuring Relay Timings

### Setting Loop Cycle Time
Enter the total duration (in seconds) for one complete timing cycle in the **Loop Time (s)** field.

### Configuring Channels
In the **Relay Channels Table**:
- **Enable Checkbox**: Turn individual channels ON or OFF. Disabled channels remain OFF (`0, 0`).
- **Start Time (s)**: The second within the cycle when the relay energizes.
- **Stop Time (s)**: The second within the cycle when the relay de-energizes.

> **Note**: Validation rules require that `Stop Time` must be greater than `Start Time`, and both must fall within `[0, Loop Time]`.

---

## 6. Project File Management & Crash Recovery

### Saving & Opening Projects
- **Save Project (`Ctrl+S`)**: Saves the full configuration schema to a `.json` file.
- **Open Project (`Ctrl+O`)**: Restores complete configuration state from a saved `.json` project file.

### Undo / Redo
- **Undo (`Ctrl+Z`)**: Reverts the last configuration modification.
- **Redo (`Ctrl+Y`)**: Re-applies the undone change.

### Automatic Crash Recovery
If the computer shuts down unexpectedly or the application is closed forcibly:
- Relay Controller Studio continuously autosaves transient state.
- Upon reopening, a prompt will ask: *"An unsaved project session was found... Would you like to recover this project?"* Click **Yes** to restore your work seamlessly.

---

## 7. Firmware Compilation & Flashing

1. Connect your Arduino or ESP32 board to a USB port.
2. Click **Refresh / Detect** in the Board Panel to auto-detect the COM port.
3. Verify your timing configuration shows **Configuration Valid**.
4. Click **Upload Firmware**.
5. The application will:
   - Modify only configuration header constants in the `.ino` firmware sketch (preserving firmware logic).
   - Run background non-blocking compilation via `arduino-cli`.
   - Automatically attempt flashing (for Arduino Nano, it automatically retries with new/old bootloader if needed).
   - Display real-time progress and success notification.

---

## 8. Troubleshooting & Driver Installation

### Port Not Detected
- Ensure your USB cable supports data transfer (some micro-USB cables are power-only).
- Check Windows Device Manager under **Ports (COM & LPT)**.
- If using CH340 or CP2102 USB-to-Serial chips (common on Nano and ESP32), ensure the appropriate USB driver is installed.

### Port Busy / Permission Denied
- Close any external Serial Monitors (e.g. Arduino IDE Serial Monitor or PuTTY) that may be holding the COM port open.

---
*Relay Controller Studio - Industrial Automation Made Simple.*
