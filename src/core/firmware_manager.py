"""
firmware_manager.py
================================================================================
Manages discovery of firmware templates on disk and non-destructive header
constant rewriting/parsing for Arduino (.ino) sketches.
================================================================================
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from core.constants import BOARD_FIRMWARE_FOLDER, FIRMWARE_DIR, firmware_folder_name
from core.logger import get_logger
from core.models import RelayConfiguration, RelayObject

logger = get_logger()


class FirmwareCatalog:
    """
    Discovers available firmware builds on disk.
    """

    def __init__(self, firmware_root: Path = FIRMWARE_DIR):
        self._root = firmware_root

    def available_channel_counts(self, board: str) -> List[int]:
        """
        Return the list of channel counts that have a real firmware
        folder on disk for the given board, e.g. [2, 4, 8, 16].
        """
        board_folder = BOARD_FIRMWARE_FOLDER.get(board)
        if not board_folder:
            logger.warning("Unknown board '%s' in available_channel_counts()", board)
            return []

        board_path = self._root / board_folder
        if not board_path.exists():
            logger.warning("Firmware folder missing: %s", board_path)
            return []

        found = []
        for entry in sorted(board_path.iterdir()):
            if entry.is_dir() and entry.name.endswith("CH"):
                try:
                    count = int(entry.name.replace("CH", ""))
                    found.append(count)
                except ValueError:
                    continue
        return sorted(found)

    def sketch_path(self, board: str, channel_count: int) -> Path:
        """
        Return the expected path to the .ino sketch for a given board and
        channel count, e.g. firmware/UNO/4CH/RelayController_4CH.ino
        """
        board_folder = BOARD_FIRMWARE_FOLDER.get(board, "")
        folder = firmware_folder_name(channel_count)
        sketch_name = f"RelayController_{folder}.ino"
        return self._root / board_folder / folder / sketch_name

    def sketch_exists(self, board: str, channel_count: int) -> bool:
        return self.sketch_path(board, channel_count).is_file()


class FirmwareConfigurator:
    """
    Locates user configuration variables inside the target .ino file and rewrites
    or parses them, establishing bidirectional sync between disk and GUI configuration models.
    """

    def __init__(self, catalog: FirmwareCatalog):
        self._catalog = catalog

    def apply_profile(self, profile: RelayConfiguration) -> bool:
        """
        Open the .ino file matching profile's board and channel count,
        locate the configuration variables, and rewrite them without modifying logic.
        """
        sketch_path = self._catalog.sketch_path(profile.board_type, profile.firmware_type)
        if not sketch_path.is_file():
            logger.error("Sketch file not found: %s", sketch_path)
            return False

        try:
            content = sketch_path.read_text(encoding="utf-8")

            # Replace Total Time
            content = re.sub(
                r"(unsigned\s+long\s+TOTAL_TIME_SECONDS\s*=\s*)\d+(\s*;)",
                rf"\g<1>{profile.loop_time}\g<2>",
                content
            )

            # Replace Active Low
            active_low_str = "true" if profile.relay_active_low else "false"
            content = re.sub(
                r"(bool\s+RELAY_ACTIVE_LOW\s*=\s*)(true|false)(\s*;)",
                rf"\g<1>{active_low_str}\g<3>",
                content
            )

            # Replace Brightness
            content = re.sub(
                r"(uint8_t\s+DISPLAY_BRIGHTNESS\s*=\s*)\d+(\s*;)",
                rf"\g<1>{profile.display_brightness}\g<2>",
                content
            )

            # Replace Countdown Enable
            countdown_str = "true" if profile.countdown_enable else "false"
            content = re.sub(
                r"(bool\s+COUNTDOWN_DISPLAY_ENABLED\s*=\s*)(true|false)(\s*;)",
                rf"\g<1>{countdown_str}\g<3>",
                content
            )

            # Replace Relay Timings
            start_times = ", ".join(str(r.start_time) for r in profile.relay_list)
            stop_times = ", ".join(str(r.stop_time) for r in profile.relay_list)

            content = re.sub(
                r"(unsigned\s+long\s+RelayStartTime\[[^\]]*\]\s*=\s*\{)[^\}]*(\};)",
                rf"\g<1>{start_times}\g<2>",
                content
            )
            content = re.sub(
                r"(unsigned\s+long\s+RelayStopTime\[[^\]]*\]\s*=\s*\{)[^\}]*(\};)",
                rf"\g<1>{stop_times}\g<2>",
                content
            )

            sketch_path.write_text(content, encoding="utf-8")
            logger.info("FirmwareConfigurator: Applied profile to %s", sketch_path)
            return True
        except Exception as e:
            logger.exception("Failed to write profile config to sketch: %s", e)
            return False

    def read_current_config(self, board: str, channel_count: int) -> RelayConfiguration:
        """
        Read the actual .ino file from disk and parse variables back into a RelayConfiguration.
        """
        sketch_path = self._catalog.sketch_path(board, channel_count)
        if not sketch_path.is_file():
            logger.warning("Sketch not found at %s. Creating default config.", sketch_path)
            return RelayConfiguration.create_default(board, channel_count)

        try:
            content = sketch_path.read_text(encoding="utf-8")

            # Parse simple fields
            m_loop = re.search(r"TOTAL_TIME_SECONDS\s*=\s*(\d+)", content)
            m_active = re.search(r"RELAY_ACTIVE_LOW\s*=\s*(true|false)", content)
            m_bright = re.search(r"DISPLAY_BRIGHTNESS\s*=\s*(\d+)", content)
            m_count = re.search(r"COUNTDOWN_DISPLAY_ENABLED\s*=\s*(true|false)", content)

            loop_time = int(m_loop.group(1)) if m_loop else 30
            active_low = (m_active.group(1) == "true") if m_active else True
            brightness = int(m_bright.group(1)) if m_bright else 7
            countdown_enable = (m_count.group(1) == "true") if m_count else True

            # Parse arrays
            m_start = re.search(r"RelayStartTime\[[^\]]*\]\s*=\s*\{([^\}]*)\}", content)
            m_stop = re.search(r"RelayStopTime\[[^\]]*\]\s*=\s*\{([^\}]*)\}", content)

            start_vals = []
            if m_start:
                start_vals = [int(x.strip()) for x in m_start.group(1).split(",") if x.strip()]
            stop_vals = []
            if m_stop:
                stop_vals = [int(x.strip()) for x in m_stop.group(1).split(",") if x.strip()]

            relays = []
            for i in range(channel_count):
                start = start_vals[i] if i < len(start_vals) else 0
                stop = stop_vals[i] if i < len(stop_vals) else 0
                enabled = not (start == 0 and stop == 0)
                relays.append(RelayObject(relay_number=i, enabled=enabled, start_time=start, stop_time=stop))

            config = RelayConfiguration(
                board_type=board,
                firmware_type=channel_count,
                loop_time=loop_time,
                relay_active_low=active_low,
                display_brightness=brightness,
                countdown_enable=countdown_enable,
                relay_list=relays
            )
            logger.info("FirmwareConfigurator: Loaded config from %s", sketch_path)
            return config
        except Exception as e:
            logger.warning("Failed to parse config from sketch: %s. Returning defaults.", e)
            return RelayConfiguration.create_default(board, channel_count)
