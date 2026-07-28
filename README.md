# Relay Controller Studio

> A professional desktop application for configuring, validating, compiling, and flashing multi-channel relay controller firmware for Arduino UNO/Nano and ESP32 boards.

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Qt](https://img.shields.io/badge/PySide6-Qt6-green)
![Arduino](https://img.shields.io/badge/Arduino-CLI-orange)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## Overview

Relay Controller Studio is a complete Windows desktop application that enables users to design complex relay timing sequences without writing Arduino code.

The software automatically validates configurations, generates firmware with user-defined settings, and uploads it directly to supported microcontrollers through an intuitive graphical interface.

The application is designed for engineers, automation developers, students, industrial control systems, exhibitions, lighting installations, and custom relay-based automation projects.

---

# Features

## Modern Desktop Interface

- Professional Qt-based user interface
- Real-time configuration editing
- Interactive relay event editor
- Timeline visualization
- Live validation feedback
- Project save/load support
- Automatic startup wizard

---

## Supported Hardware

### Arduino

- Arduino UNO
- Arduino Nano

### ESP32

- ESP32 Dev Module

Supported relay variants

- 2 Channel
- 4 Channel
- 8 Channel
- 16 Channel

---

## Relay Configuration

Configure every relay independently.

Supports

- Multiple ON/OFF events per relay
- Individual event scheduling
- Oscillation mode
- Adjustable oscillation period
- Disabled events
- Active High / Active Low relays

---

## Countdown Display

Supports TM1637 4-digit displays.

Features include

- Countdown timer
- Adjustable brightness
- Enable / Disable display
- Error indication

---

## Timeline Editor

Interactive timeline showing

- Relay activation windows
- Event ordering
- Overlapping detection
- Loop duration

---

## Automatic Validation

The software validates every configuration before upload.

Checks include

- Invalid event ranges
- Event overlap
- Start < Stop
- Loop duration limits
- Oscillation validation
- Missing configuration
- Invalid relay timings

---

## Upload System

Integrated upload pipeline.

Features

- Automatic board detection
- Automatic COM port detection
- Firmware generation
- Arduino CLI integration
- Progress reporting
- Upload logs
- Error handling

---

## Project Management

Projects can be saved and reopened at any time.

Includes

- JSON project format
- Automatic recovery
- Recent projects
- Import / Export

---

# Firmware Features

The generated firmware includes

- Millisecond timing engine
- Multiple relay events
- Oscillation support
- Active Low / High support
- TM1637 countdown display
- Runtime validation
- Error protection

---

# Technology Stack

Desktop

- Python 3.12+
- PySide6 (Qt6)

Embedded

- Arduino Framework
- ESP32 Arduino Core

Tools

- Arduino CLI
- avrdude
- esptool

---

# Project Structure

```
Relay_Controller_Studio/
│
├── firmware/
├── src/
│   ├── core/
│   ├── ui/
│   ├── resources/
│   └── widgets/
│
├── assets/
├── config/
├── tests/
├── tools/
├── build/
└── docs/
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/Electropool/REALY-CONTROLER.git
```

Install dependencies

```bash
pip install -r requirements.txt
```

Launch the application

```bash
python main.py
```

---

# Screenshots

> Screenshots will be added soon.

---

# Roadmap

- Binary firmware distribution (.HEX / .BIN)
- Firmware patching without source distribution
- Additional microcontroller support
- More relay board variants
- Custom firmware templates
- Automatic update system

---

# Contributing

Contributions, suggestions, feature requests, and bug reports are welcome.

Please open an Issue or submit a Pull Request.

---

# License

This project is licensed under the MIT License.

---

# Author

**Arpan Kar**

Electronics & Embedded Systems Developer

GitHub:
https://github.com/Electropool

Website:
https://electropool.online

LinkedIn:
https://www.linkedin.com/in/arpan-kar-1806a628b/

---

If you find this project useful, consider giving it a ⭐ on GitHub.- **Smart Bootloader Fallback**: Automatically retries Arduino Nano uploads across standard and old bootloader configurations.
- **Non-Blocking Flashing**: Full multi-threaded compilation and flashing keep the Qt GUI 100% responsive.

### 2. Complete Project System & Undo/Redo
- **JSON Project Files**: Save (`Ctrl+S`), Save As (`Ctrl+Shift+S`), Open (`Ctrl+O`), and New (`Ctrl+N`) project files.
- **Undo / Redo Engine**: Full history stack for reverting and re-applying timing edits (`Ctrl+Z` / `Ctrl+Y`).
- **Automatic Crash Recovery**: Continuous session autosaving protects work against unexpected system crashes or loss of power.

### 3. Live Validation & Real-time Console
- **Real-Time Timing Validation**: Instant error checking for range constraints, start/stop order, and total loop duration.
- **Interactive UI Feedback**: Red border error indicators on invalid cells with itemized validation panel summaries.
- **Streaming Console Panel**: Real-time line-by-line compiler and flasher stdout logging attached directly to the application logger.

### 4. Production Deployment & First Startup Wizard
- **Zero Dependencies**: Standalone Windows executables (`Release` and `Debug` builds).
- **First Startup Wizard**: Automatically initializes the portable Arduino CLI, core packages (`arduino:avr`, `esp32:esp32`), and required libraries (`TM1637`).
- **Update Checker**: Automated background and manual release checks against the GitHub repository.

---

## Project Structure

```
Relay_Controller/
├── main.py                  # Application entry point & wizard bootstrap
├── run.bat                  # Developer launcher script
├── build_release.bat        # Windows release build (No console window)
├── build_debug.bat          # Windows debug build (With console log output)
├── build.bat                # Standard build script
├── requirements.txt         # Dependencies (PySide6, pyserial, pyinstaller)
├── README.md
├── docs/
│   └── UserManual.md        # Complete User Manual & Guide
│
├── src/
│   ├── core/                # Core logic (Model-View architecture)
│   │   ├── constants.py     # Global constants & path resolution
│   │   ├── models.py        # RelayConfiguration & RelayObject models
│   │   ├── validation_manager.py # Validation engine
│   │   ├── firmware_manager.py   # Firmware catalog & C++ regex configurator
│   │   ├── board_detector.py     # Auto COM port & board detection
│   │   ├── uploader.py           # Portable Arduino CLI uploader & QThread worker
│   │   ├── update_checker.py     # GitHub release checker
│   │   ├── settings_manager.py   # Settings persistence
│   │   └── logger.py             # App logger & Qt handlers
│   │
│   └── ui/                  # PySide6 Presentation Layer
│       ├── main_window.py   # Top-level window & menu bar
│       ├── resources/
│       │   └── theme.qss    # Modern dark stylesheet
│       └── widgets/
│           ├── startup_wizard.py    # First Startup Wizard dialog
│           ├── board_panel.py       # Board selection & status
│           ├── firmware_panel.py    # Global configuration controls
│           ├── relay_table.py       # Per-channel timing table
│           ├── validation_panel.py  # Error summary panel
│           └── console_panel.py     # Live log output panel
│
├── firmware/                # C++ Arduino Sketch templates (.ino)
│   ├── UNO/                 # 2CH, 4CH, 8CH, 16CH
│   └── ESP32/               # 2CH, 4CH, 8CH, 16CH
│
├── config/                  # Settings & autosave recovery files
├── tools/                   # Portable Arduino CLI & toolchain directory
└── logs/                    # Runtime log files
```

---

## Getting Started

### Prerequisites

- **Windows 10/11**
- **Python 3.12+** (For running from source)

### Running from Source

```bash
# Option 1: Use the developer launcher
run.bat

# Option 2: Manual command line
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Building Executables

```bash
# Build standalone Release executable (GUI only):
build_release.bat
# Output: build\dist\RelayControllerStudio_Release.exe

# Build Debug executable (Console output enabled):
build_debug.bat
# Output: build\dist\RelayControllerStudio_Debug.exe
```

---

## License

All rights reserved — [Electropool Repository](https://github.com/Electropool/RELAY-CONTROLLER-STUDIO.git).
