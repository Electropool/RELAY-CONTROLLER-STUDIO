# Relay Controller Studio

A desktop GUI application for configuring and uploading firmware to Arduino UNO/Nano and ESP32-based relay controller boards.

Built with **Python 3.12+** and **PySide6 (Qt6)**.

---

## Features

### Phase 1 — GUI Foundation
- Board selection panel (Arduino UNO/Nano, ESP32)
- Firmware selection by channel count (2, 4, 8, 16 relays)
- Relay timing table with per-channel Start/Stop configuration
- Firmware parameter controls (Loop Time, Active Low, Brightness, Countdown)
- Internal console with live logging
- Persistent user settings (window size, last board, auto-detect preference)
- Dark themed Qt stylesheet

### Phase 2.1 — GUI Configuration System
- Working board selector with application state updates
- Firmware type selector (channel count) dynamically populated per board
- Loop Time, Active Low, Brightness, and Countdown controls wired to state
- Relay table auto-populates rows based on selected channel count

### Phase 2.2 — Validation Engine
- Live validation on every parameter change (no Apply button needed)
- Loop Time range check (1–9999 seconds)
- Relay rules: Start ≤ Stop, Stop ≤ Loop Time, no negative values
- Disabled relays (0/0) are skipped automatically
- Visual feedback: red borders and tooltips on invalid fields
- Validation summary panel with error count and itemized messages
- Upload button disabled when validation fails

### Phase 2.3 — Configuration Data Model
- `RelayConfiguration` class as single source of truth
- `RelayObject` per-channel data model
- Automatic bidirectional sync between model and GUI
- Project state tracking (Modified / Saved)
- Default configuration generation per channel count
- Console messages: Configuration Created, Configuration Updated, Relay Added/Removed, Project Modified

---

## Upcoming Phases

> These are planned but **not yet implemented**:

- JSON Save / Load
- Firmware `.ino` file editing
- Arduino CLI integration
- Firmware upload (compile + flash)
- Board auto-detection via COM ports
- Timeline preview
- Undo / Redo

---

## Project Structure

```
Relay_Controller/
├── main.py                  # Application entry point
├── run.bat                  # Windows launcher (creates venv, installs deps, runs)
├── build.bat                # PyInstaller packaging script
├── requirements.txt         # Python dependencies
├── .gitignore
│
├── src/
│   ├── core/                # Logic layer (no Qt dependency)
│   │   ├── constants.py     # App-wide constants and paths
│   │   ├── models.py        # RelayConfiguration, RelayObject, BoardInfo
│   │   ├── validation_manager.py  # Input validation engine
│   │   ├── firmware_manager.py    # Firmware catalog and configurator
│   │   ├── board_detector.py      # Board detection (placeholder)
│   │   ├── uploader.py            # Upload logic (placeholder)
│   │   ├── settings_manager.py    # Persistent user settings
│   │   └── logger.py              # Centralized logging
│   │
│   └── ui/                  # Presentation layer (PySide6 / Qt)
│       ├── main_window.py   # Main application window
│       ├── resources/
│       │   └── theme.qss    # Dark theme stylesheet
│       └── widgets/
│           ├── board_panel.py       # Board selection + status
│           ├── firmware_panel.py    # Firmware config controls
│           ├── relay_table.py       # Relay timing table
│           ├── validation_panel.py  # Validation summary display
│           └── console_panel.py     # Log output console
│
├── firmware/                # Arduino .ino source files
│   ├── UNO/
│   │   ├── 2CH/ 4CH/ 8CH/ 16CH/
│   └── ESP32/
│       ├── 2CH/ 4CH/ 8CH/ 16CH/
│
├── config/
│   └── default_settings.json
├── assets/icons/
├── drivers/
├── tools/
├── build/
└── logs/
```

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- **Windows** (tested on Windows 10/11)

### Run from Source

```bash
# Option 1: Use the launcher script (recommended)
run.bat

# Option 2: Manual setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Build Windows Executable

```bash
build.bat
# Output: build\dist\RelayControllerStudio.exe
```

---

## Architecture

The application follows a strict **Model–View** separation:

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Core** | `src/core/` | Data models, validation, business logic. Zero Qt dependency. |
| **UI** | `src/ui/` | Qt widgets, layout, signal/slot wiring. No business logic. |
| **Entry** | `main.py` | Bootstrap only: sys.path setup, QApplication, theme loading. |

The `RelayConfiguration` dataclass is the **single source of truth**. The GUI reads from and writes to this model. Validation runs against the model, not the GUI widgets.

---

## License

This project is currently private. All rights reserved.