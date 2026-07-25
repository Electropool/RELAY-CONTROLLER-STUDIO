# Relay Controller Studio

A desktop application for configuring relay timings and flashing the
**Relay Controller** firmware family onto **Arduino UNO/Nano** and
**ESP32** boards — no Arduino IDE knowledge required by the end user.

> **Phase status: PHASE 1 — Architecture & GUI only.**
> Board detection, firmware compilation, and firmware flashing are **not**
> implemented yet. Every relevant function/class exists as a documented
> placeholder. See [Phase 1 scope](#phase-1-scope) below.

---

## Table of contents

- [Phase 1 scope](#phase-1-scope)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Architecture overview](#architecture-overview)
- [The firmware folder](#the-firmware-folder)
- [Building a Windows executable](#building-a-windows-executable)
- [Roadmap](#roadmap)
- [Adding a new board family](#adding-a-new-board-family)

---

## Phase 1 scope

**In scope for this phase:**
- Full project architecture and folder structure.
- A working, modern PySide6 GUI: board selection, firmware/channel
  selection, dynamic relay configuration table, console panel, progress
  bar, refresh/upload buttons.
- A real settings manager (persists theme, window size, last board/port,
  auto-detect preference to `config/user_settings.json`).
- A real logging system (`logs/app.log`, rotating, mirrored live into the
  in-app console panel).
- A real firmware **catalog** that reads what firmware actually exists on
  disk under `firmware/` so the GUI's dropdowns are always accurate.
- Placeholder classes/functions for board detection, firmware
  configuration (rewriting), and uploading — fully documented, wired into
  the GUI, but not functional yet.
- The original, unmodified firmware sketches, organized under `firmware/`.

**Explicitly NOT in scope for this phase:**
- No board detection logic (`detectArduino()` / `detectESP32()` are
  placeholders that always report "not connected").
- No Arduino CLI integration.
- No esptool integration.
- No firmware compilation.
- No firmware flashing.
- No firmware **file editing** — the `.ino` files under `firmware/` are
  byte-for-byte what was supplied and must not be modified by this tool
  in this phase.

The application **will launch and be fully navigable** with these
placeholders in place — buttons and dropdowns all work, they just don't
talk to real hardware or a compiler yet.

---

## Project structure

```
RelayControllerStudio/
├── main.py                  # Application entry point (thin — no logic)
├── requirements.txt
├── run.bat                  # Windows: create venv, install deps, launch
├── build.bat                # Windows: PyInstaller packaging
├── README.md                # You are here
│
├── src/
│   ├── core/                 # GUI-agnostic logic layer
│   │   ├── constants.py       # Boards, channel counts, paths, status labels
│   │   ├── models.py          # RelayChannelConfig, FirmwareProfile, BoardInfo
│   │   ├── logger.py          # Rotating file + console logging setup
│   │   ├── settings_manager.py# Persists AppSettings to config/user_settings.json
│   │   ├── board_detector.py  # PLACEHOLDER: detectArduino(), detectESP32()
│   │   ├── uploader.py        # PLACEHOLDER: ArduinoUploader, ESP32Uploader
│   │   └── firmware_manager.py# FirmwareCatalog (real) + FirmwareConfigurator (PLACEHOLDER)
│   │
│   └── ui/                   # Qt/PySide6 presentation layer
│       ├── main_window.py     # Assembles panels, wires signals to core/
│       ├── resources/
│       │   └── theme.qss       # Dark theme stylesheet
│       └── widgets/
│           ├── board_panel.py     # Board dropdown, status, Refresh/Upload buttons
│           ├── firmware_panel.py  # Channel-count dropdown, loop time, polarity
│           ├── relay_table.py     # Dynamic per-relay Start/Stop/Enabled table
│           └── console_panel.py   # Live log console (reads from logging module)
│
├── firmware/                 # UNMODIFIED firmware, as supplied
│   ├── UNO/{2CH,4CH,8CH,16CH}/RelayController_*.ino
│   └── ESP32/{2CH,4CH,8CH,16CH}/RelayController_*.ino
│
├── assets/
│   ├── icons/                 # App icon(s) — placeholder, add app_icon.ico here
│   └── styles/                # Reserved for additional/alternate themes
│
├── tools/                     # Reserved for arduino-cli / esptool (future)
├── drivers/                   # Reserved for CH340/CP210x driver installers (future)
├── config/
│   ├── default_settings.json  # Shipped defaults (read-only reference)
│   └── user_settings.json     # Generated at runtime, not committed
├── logs/
│   └── app.log                 # Generated at runtime, rotating
└── build/                     # PyInstaller output (generated, not committed)
```

---

## Getting started

### Requirements
- Python 3.10+
- Windows, macOS, or Linux (development); Windows is the target for the
  packaged executable.

### Run from source

**Windows:**
```bat
run.bat
```
This creates a local `.venv`, installs `requirements.txt`, and launches
the app. Re-run it any time — it only re-installs dependencies the first
time.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## Architecture overview

The project follows a strict **GUI / logic separation**:

- **`src/core/`** contains zero Qt imports. Every class here (settings,
  logging, models, the board/upload/firmware placeholders) can be
  unit-tested or reused from a future CLI without a display attached.
- **`src/ui/`** contains only presentation code. Widgets expose Qt
  **signals** for user actions (`boardChanged`, `uploadRequested`,
  `configChanged`, …) and simple setter methods for updating what's on
  screen. `main_window.py` is the only place that connects UI signals to
  `core/` behavior — individual widgets never import each other or reach
  into `core/` directly.
- **Logging is the single source of truth for console output.** Any
  module calls `core.logger.get_logger()` and logs normally; the GUI's
  `ConsolePanel` attaches its own `logging.Handler` (via a thread-safe Qt
  signal, so future background threads can log safely) rather than the
  reverse. This means board detection, upload progress, and errors will
  "just show up" in the console once implemented, with no GUI-side
  changes needed.
- **Data flows through plain dataclasses** (`RelayChannelConfig`,
  `FirmwareProfile`, `BoardInfo` in `core/models.py`), not raw dicts or
  Qt widget references, so the eventual `FirmwareConfigurator` and
  uploader implementations have a stable, typed contract to work against.

### Signal/slot map (high level)

| Widget            | Signal                | Handled by (MainWindow slot)     |
|--------------------|------------------------|-----------------------------------|
| `BoardPanel`        | `boardChanged`          | `_on_board_changed`                |
| `BoardPanel`        | `refreshRequested`      | `_on_refresh_requested`            |
| `BoardPanel`        | `uploadRequested`       | `_on_upload_requested`             |
| `FirmwarePanel`     | `channelCountChanged`   | `_on_channel_count_changed`        |
| `FirmwarePanel`     | `loopTimeChanged`       | `_on_config_field_changed`         |
| `FirmwarePanel`     | `activeLowChanged`      | `_on_config_field_changed`         |
| `RelayTableWidget`  | `configChanged`         | `_on_config_field_changed`         |

---

## The firmware folder

`firmware/` contains the **exact, unmodified** `.ino` sketches supplied
for this project, organized as:

```
firmware/<BOARD>/<N>CH/RelayController_<N>CH.ino
```

`core/firmware_manager.py`'s `FirmwareCatalog` class scans this structure
at runtime to populate the GUI's dropdowns — so the set of available
channel counts always matches what's actually on disk. Every sketch
documents its own editable configuration block (`AUTO GENERATED CONFIG`
on ESP32 builds, `USER CONFIGURATION` on UNO builds) — this is what a
future `FirmwareConfigurator` implementation will locate and rewrite
before compilation. **No code in this phase reads or writes those
blocks.**

---

## Building a Windows executable

Packaging uses [PyInstaller](https://pyinstaller.org/) in `--onefile`
mode. Once dependencies are installed (via `run.bat` or manually):

```bat
build.bat
```

This produces `build\dist\RelayControllerStudio.exe` — a single file a
technician can run with no Python installation of their own. The script
bundles the `ui/resources` stylesheet, `firmware/`, and `config/`
default-settings folders alongside the executable via `--add-data`.

On macOS/Linux, the equivalent manual command (note the `:` separator
instead of Windows' `;`) is:
```bash
pyinstaller --name RelayControllerStudio --onefile --windowed \
    --add-data "src/ui/resources:ui/resources" \
    --add-data "firmware:firmware" \
    --add-data "config:config" \
    --paths "src" \
    main.py
```

---

## Roadmap

Planned for later phases (not implemented yet, in rough order):

1. **Board detection** — implement `detectArduino()` / `detectESP32()`
   using `pyserial`'s port enumeration + known VID/PID tables, run on a
   background `QThread`.
2. **Firmware configuration writing** — implement
   `FirmwareConfigurator.apply_profile()` to locate and rewrite the
   config block of the target `.ino` file from a `FirmwareProfile`.
3. **Compilation & upload** — implement `ArduinoUploader` /
   `ESP32Uploader` around `arduino-cli` (and `esptool.py` for ESP32
   flashing specifics), streaming output into the console via
   `QProcess`.
4. **Driver bundling** — populate `drivers/` and add a guided "Install
   Drivers" flow for CH340/CP210x/FTDI chips.
5. **Packaging polish** — app icon, versioned installer (e.g. Inno
   Setup) wrapping the PyInstaller `.exe`.

---

## Adding a new board family

The architecture was designed so that adding **STM32**, **RP2040**, or
**ESP8266** support later does not require restructuring:

1. Add the board's display name to `SUPPORTED_BOARDS` and a matching
   entry in `BOARD_FIRMWARE_FOLDER` in `core/constants.py`.
2. Create `firmware/<NEW_BOARD_FOLDER>/<N>CH/` folders with the matching
   sketches — `FirmwareCatalog` will pick them up automatically.
3. Add a board-specific subclass of `BaseUploader` in `core/uploader.py`
   (mirroring `ArduinoUploader` / `ESP32Uploader`) once real flashing is
   implemented.
4. No changes are required in `ui/` — every widget already reads its
   options from `core/constants.py` and `FirmwareCatalog` rather than
   hard-coding board names.
