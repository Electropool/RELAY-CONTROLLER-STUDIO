"""
settings_manager.py
================================================================================
Persists and restores user-facing application settings (theme, window size,
last-used board/port, etc.) to a JSON file under config/.

This is a real, working implementation (not a placeholder) because settings
persistence has no dependency on the firmware-flashing pieces that are
explicitly out of scope for Phase 1 -- it is pure application plumbing.
================================================================================
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict

from core.constants import CONFIG_DIR, USER_SETTINGS_FILE
from core.logger import get_logger

logger = get_logger()


@dataclass
class AppSettings:
    """
    Every persisted setting the application currently knows about. New
    settings should be added here as typed fields (with sensible defaults)
    rather than as loose dictionary keys, so callers get IDE autocomplete
    and type-checking instead of magic strings.
    """

    theme: str = "dark"
    window_width: int = 1280
    window_height: int = 800
    remember_last_board: bool = True
    last_board: str = ""
    remember_last_port: bool = True
    last_com_port: str = ""
    auto_detect_on_launch: bool = True


class SettingsManager:
    """
    Loads AppSettings from disk on construction and writes them back out on
    save(). Falls back to defaults (and logs a warning) if the settings
    file is missing or corrupt, so a bad/edited JSON file can never prevent
    the application from starting.
    """

    def __init__(self, settings_path=USER_SETTINGS_FILE):
        self._path = settings_path
        self.settings = self._load()

    def _load(self) -> AppSettings:
        if not self._path.exists():
            logger.info("No existing settings file found, using defaults.")
            return AppSettings()

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
            # Only keep keys that AppSettings actually defines, so removed /
            # renamed settings in future versions don't raise TypeErrors.
            valid_keys = AppSettings.__dataclass_fields__.keys()
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            settings = AppSettings(**filtered)
            logger.info("Settings loaded from %s", self._path)
            return settings
        except (json.JSONDecodeError, OSError, TypeError) as exc:
            logger.warning(
                "Failed to load settings (%s); falling back to defaults.", exc
            )
            return AppSettings()

    def save(self) -> None:
        """Write the current settings to disk as pretty-printed JSON."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(asdict(self.settings), f, indent=4)
            logger.info("Settings saved to %s", self._path)
        except OSError as exc:
            logger.error("Failed to save settings: %s", exc)

    def update(self, **kwargs) -> None:
        """
        Update one or more settings fields by keyword and persist
        immediately. Unknown keys are ignored with a warning rather than
        raising, so a typo in calling code degrades gracefully.
        """
        valid_keys = AppSettings.__dataclass_fields__.keys()
        for key, value in kwargs.items():
            if key in valid_keys:
                setattr(self.settings, key, value)
            else:
                logger.warning("Ignoring unknown setting key: %s", key)
        self.save()
