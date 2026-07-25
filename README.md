# Relay Controller Studio

A complete, standalone desktop application for configuring, validating, and flashing multi-channel relay timing systems for Arduino UNO/Nano and ESP32 hardware without needing Python or the Arduino IDE.

**GitHub Repository**: [https://github.com/Electropool/REALY-CONTROLER.git](https://github.com/Electropool/REALY-CONTROLER.git)

Built with **Python 3.12+**, **PySide6 (Qt6)**, and **Arduino CLI**.

---

## Key Features

### 1. Hardware Integration & Flashing Layer
- **Automatic Board & COM Port Detection**: Scans system serial ports to auto-identify Arduino UNO, Arduino Nano, and ESP32 microcontrollers.
- **Embedded Portable Arduino CLI**: Bundled toolchain initialization with non-blocking compilation and flashing.
- **In-Memory C++ Header Injection**: Dynamically updates configuration parameters directly inside target `.ino` sketches without altering firmware execution logic.
- **Smart Bootloader Fallback**: Automatically retries Arduino Nano uploads across standard and old bootloader configurations.
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

All rights reserved — [Electropool Repository](https://github.com/Electropool/REALY-CONTROLER.git).