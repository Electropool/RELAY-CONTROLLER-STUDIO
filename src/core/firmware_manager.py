"""
firmware_manager.py
================================================================================
PHASE 1 PLACEHOLDER MODULE.

Defines the architecture for two related-but-distinct responsibilities:

  1. FirmwareCatalog  -- (REAL, implemented) discovers which firmware
     builds physically exist under firmware/<BOARD>/<N>CH/ so the GUI's
     board/firmware selectors always reflect what's actually on disk
     rather than a hard-coded list that could drift out of sync.

  2. FirmwareConfigurator -- (PLACEHOLDER, NOT implemented) will be
     responsible for rewriting a given .ino file's "AUTO GENERATED
     CONFIG" / "USER CONFIGURATION" block to match a FirmwareProfile
     edited in the GUI, before that file is handed to an uploader.

Per the project requirements for this phase, FirmwareConfigurator must
NOT modify any firmware file yet -- only its class shape is defined here.
================================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from core.constants import BOARD_FIRMWARE_FOLDER, FIRMWARE_DIR, firmware_folder_name
from core.logger import get_logger
from core.models import RelayConfiguration

logger = get_logger()


class FirmwareCatalog:
    """
    Discovers available firmware builds on disk. This is a real (not
    placeholder) implementation, since populating the GUI's dropdowns with
    firmware that genuinely exists is needed even in Phase 1.
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
        channel count, e.g.
        firmware/UNO/4CH/RelayController_4CH.ino

        Does not guarantee the file exists -- callers should check.
        """
        board_folder = BOARD_FIRMWARE_FOLDER.get(board, "")
        folder = firmware_folder_name(channel_count)
        sketch_name = f"RelayController_{folder}.ino"
        return self._root / board_folder / folder / sketch_name

    def sketch_exists(self, board: str, channel_count: int) -> bool:
        return self.sketch_path(board, channel_count).is_file()


class FirmwareConfigurator:
    """
    PLACEHOLDER.

    Will eventually locate the "AUTO GENERATED CONFIG START/END" (ESP32
    sketches) or "USER CONFIGURATION" (UNO sketches) markers inside a
    target .ino file and rewrite the values between them -- NUM_RELAYS,
    TOTAL_TIME_SECONDS, RELAY_ACTIVE_LOW, RelayStartTime[]/RelayStopTime[]
    -- to match a FirmwareProfile assembled from the GUI's relay table.

    Explicitly NOT implemented in this phase. No firmware file may be
    modified by this class yet.
    """

    def __init__(self, catalog: FirmwareCatalog):
        self._catalog = catalog

    def apply_profile(self, profile: RelayConfiguration) -> bool:
        """
        [PLACEHOLDER]
        In a future phase, this method will open the .ino file matching
        `profile.board` / `profile.channel_count`, locate the configuration block,
        and rewrite the loop time, polarity, and relay arrays before compilation.
        """
        logger.info(
            "FirmwareConfigurator: (Placeholder) applied profile board=%s channels=%s",
            profile.board_type,
            profile.firmware_type,
        )
        return True

    def read_current_config(self, board: str, channel_count: int) -> RelayConfiguration:
        """
        [PLACEHOLDER]
        In a future phase, this method will read the actual .ino file from disk
        and parse the C++ config block back into a RelayConfiguration object,
        allowing the GUI to reflect the last-saved state rather than starting
        from generic zeros.

        Currently returns a clean default profile so the GUI has something
        valid to display in Phase 1.
        """
        logger.info(
            "FirmwareConfigurator: (Placeholder) reading config from disk for %s / %sCH",
            board,
            channel_count,
        )
        return RelayConfiguration.create_default(board, channel_count)
