"""
constants.py
================================================================================
Central location for every "magic value" used across the application:
board identifiers, supported channel counts, default settings, file paths,
and log levels.

Keeping these values in one module means that when the application grows to
support new boards (STM32, RP2040, ESP8266 -- see ARCHITECTURE.md) there is a
single, obvious place to register them, rather than hunting through the GUI
and logic layers for hard-coded strings.
================================================================================
"""

from __future__ import annotations

from pathlib import Path


# ------------------------------------------------------------------------
# Application metadata
# ------------------------------------------------------------------------
APP_NAME = "Relay Controller Studio"
APP_VERSION = "0.1.0-phase1"
APP_ORG = "RelayControllerStudio"

# ------------------------------------------------------------------------
# Filesystem locations (all resolved relative to the project root so the
# app behaves the same whether run from source or from a frozen
# PyInstaller executable).
# ------------------------------------------------------------------------
import sys

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

FIRMWARE_DIR = PROJECT_ROOT / "firmware"
ASSETS_DIR = PROJECT_ROOT / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
CONFIG_DIR = PROJECT_ROOT / "config"
LOGS_DIR = PROJECT_ROOT / "logs"
DRIVERS_DIR = PROJECT_ROOT / "drivers"
TOOLS_DIR = PROJECT_ROOT / "tools"

DEFAULT_SETTINGS_FILE = CONFIG_DIR / "default_settings.json"
USER_SETTINGS_FILE = CONFIG_DIR / "user_settings.json"
CRASH_RECOVERY_FILE = CONFIG_DIR / "crash_recovery.json"
LOG_FILE = LOGS_DIR / "app.log"


# ------------------------------------------------------------------------
# Supported boards.
#
# NOTE (scalability): adding a new board family (e.g. "RP2040") in a future
# phase means adding one entry here and one matching sub-folder under
# firmware/. Nothing in the GUI or logic layers should need to hard-code a
# board name outside of this table.
# ------------------------------------------------------------------------
BOARD_ARDUINO = "Arduino UNO/Nano"
BOARD_ESP32 = "ESP32"

SUPPORTED_BOARDS = [
    BOARD_ARDUINO,
    BOARD_ESP32,
]

# Sub-folder name (under firmware/) that corresponds to each board.
BOARD_FIRMWARE_FOLDER = {
    BOARD_ARDUINO: "UNO",
    BOARD_ESP32: "ESP32",
}

# ------------------------------------------------------------------------
# Supported relay channel counts.
#
# NOTE (scalability): if a 32CH build is ever added, add "32" here and drop
# a matching firmware/<BOARD>/32CH/ folder in place -- the firmware
# selector and the relay table both build themselves from this list.
# ------------------------------------------------------------------------
CHANNEL_COUNTS = [2, 4, 8, 16]

# Folder naming convention used under firmware/<BOARD>/<N>CH/
def firmware_folder_name(channel_count: int) -> str:
    """Return the firmware sub-folder name for a given channel count."""
    return f"RelayController_{channel_count}CH"


# ------------------------------------------------------------------------
# Relay electrical polarity options (mirrors RELAY_ACTIVE_LOW in firmware).
# ------------------------------------------------------------------------
POLARITY_ACTIVE_LOW = "Active LOW"
POLARITY_ACTIVE_HIGH = "Active HIGH"
POLARITY_OPTIONS = [POLARITY_ACTIVE_LOW, POLARITY_ACTIVE_HIGH]

# ------------------------------------------------------------------------
# Board connection / detection status labels, used by BoardDetector and
# reflected directly in the GUI's status indicator.
# ------------------------------------------------------------------------
STATUS_NOT_DETECTED = "Not Detected"
STATUS_DETECTING = "Detecting..."
STATUS_DETECTED = "Detected"
STATUS_ERROR = "Detection Error"

# ------------------------------------------------------------------------
# Upload / flashing status labels, used by the uploader classes and the
# progress bar + console panel.
# ------------------------------------------------------------------------
UPLOAD_IDLE = "Idle"
UPLOAD_PREPARING = "Preparing"
UPLOAD_COMPILING = "Compiling"
UPLOAD_UPLOADING = "Uploading"
UPLOAD_SUCCESS = "Success"
UPLOAD_FAILED = "Failed"

# ------------------------------------------------------------------------
# Default values applied to a freshly-selected firmware (before the user
# edits anything). These intentionally mirror the shipped .ino defaults for
# the 2CH build so the GUI never looks "empty" the first time it opens.
# ------------------------------------------------------------------------
DEFAULT_TOTAL_TIME_SECONDS = 30
DEFAULT_RELAY_ACTIVE_LOW = True
