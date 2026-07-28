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
from core.models import RelayConfiguration, RelayObject, RelayEvent

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
            if entry.is_dir() and entry.name.startswith("RelayController_") and entry.name.endswith("CH"):
                try:
                    count_str = entry.name.replace("RelayController_", "").replace("CH", "")
                    count = int(count_str)
                    found.append(count)
                except ValueError:
                    continue
        return sorted(found)

    def sketch_path(self, board: str, channel_count: int) -> Path:
        """
        Return the expected path to the .ino sketch for a given board and
        channel count, e.g. firmware/UNO/RelayController_4CH/RelayController_4CH.ino
        """
        board_folder = BOARD_FIRMWARE_FOLDER.get(board, "")
        folder = firmware_folder_name(channel_count)
        sketch_name = f"{folder}.ino"
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
            max_events = max(len(r.events) for r in profile.relay_list) if profile.relay_list else 1
            if max_events < 1:
                max_events = 1
                
            content = re.sub(
                r"(const\s+uint8_t\s+MAX_EVENTS_PER_RELAY\s*=\s*)\d+(\s*;)",
                rf"\g<1>{max_events}\g<2>",
                content
            )

            # Generate the C++ array initializer
            relay_rows = []
            for r in profile.relay_list:
                event_strings = []
                for e_idx in range(max_events):
                    if e_idx < len(r.events):
                        e = r.events[e_idx]
                        start = e.start_time if e.enabled else 0
                        stop = e.stop_time if e.enabled else 0
                        osc = "true" if e.oscillate else "false"
                        period = e.osc_period_ms
                    else:
                        start = 0
                        stop = 0
                        osc = "false"
                        period = 1000
                    event_strings.append(f"{{{start}, {stop}, {osc}, {period}}}")
                relay_rows.append(f"  {{ {', '.join(event_strings)} }}")
            
            array_initializer = "{\n" + ",\n".join(relay_rows) + "\n}"
            
            content = re.sub(
                r"(RelayEvent\s+relayEvents\[[^\]]*\]\[[^\]]*\]\s*=\s*)\{[\s\S]*?\};",
                rf"\g<1>{array_initializer};",
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
            m_events = re.search(r"relayEvents\[[^\]]*\]\[[^\]]*\]\s*=\s*\{([\s\S]*?)\};", content)
            relays = []
            if m_events:
                raw_array = m_events.group(1).strip()
                # Find each relay row: { {start, stop, osc, period}, {start, stop, osc, period} }
                relay_rows = re.findall(r"\{\s*((?:\{[^\}]*\}\s*,?\s*)+)\}", raw_array)
                for r_idx in range(channel_count):
                    events = []
                    if r_idx < len(relay_rows):
                        r_str = relay_rows[r_idx]
                        event_matches = re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(true|false)\s*,\s*(\d+)\s*\}", r_str)
                        for start_s, stop_s, osc_s, period_ms in event_matches:
                            start = int(start_s)
                            stop = int(stop_s)
                            osc = (osc_s == "true")
                            period = int(period_ms)
                            enabled = not (start == 0 and stop == 0)
                            events.append(RelayEvent(start_time=start, stop_time=stop, enabled=enabled, oscillate=osc, osc_period_ms=period))
                    
                    if not events:
                        events = [RelayEvent(start_time=0, stop_time=0, enabled=True, oscillate=False, osc_period_ms=1000)]
                    relays.append(RelayObject(relay_number=r_idx, events=events))
            else:
                # Fallback if no relayEvents block is found
                for r_idx in range(channel_count):
                    relays.append(RelayObject(relay_number=r_idx, events=[RelayEvent(start_time=0, stop_time=0, enabled=True, oscillate=False, osc_period_ms=1000)]))

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
