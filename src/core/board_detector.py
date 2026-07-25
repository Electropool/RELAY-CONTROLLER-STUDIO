"""
board_detector.py
================================================================================
PHASE 1 PLACEHOLDER MODULE.

Defines the architecture for board detection (Arduino UNO/Nano and ESP32
over USB-serial) without implementing the actual detection logic. A future
phase will fill these in using a library such as `pyserial`
(serial.tools.list_ports) to enumerate COM ports and match VID/PID pairs
or query the board for its identity.

Design notes for the future implementation:
  - detectArduino() / detectESP32() are kept as free functions (matching
    the names requested for this phase) that return a BoardInfo instance.
  - BoardDetector wraps both behind a single polling-friendly interface
    that the GUI can call from a background QThread (detection should
    never block the UI thread).
  - Detection should be re-run on demand (Refresh button) and, later,
    automatically on a timer if `auto_detect_on_launch`/polling settings
    are enabled.
================================================================================
"""

from __future__ import annotations

from core.constants import (
    BOARD_ARDUINO,
    BOARD_ESP32,
    STATUS_NOT_DETECTED,
)
from core.logger import get_logger
from core.models import BoardInfo

logger = get_logger()


def detectArduino() -> BoardInfo:
    """
    PLACEHOLDER.

    Future implementation will enumerate serial ports and identify an
    Arduino UNO/Nano by known USB VID/PID pairs (e.g. CH340, FTDI, or
    genuine Atmel/Microchip USB-serial chips), returning a populated
    BoardInfo with the matching COM port.

    Returns:
        BoardInfo: currently always a "not connected" placeholder result.
    """
    logger.debug("detectArduino() called (placeholder - no implementation yet)")
    return BoardInfo(
        board_type=BOARD_ARDUINO,
        com_port="",
        description="Detection not yet implemented (Phase 1 placeholder)",
        is_connected=False,
    )


def detectESP32() -> BoardInfo:
    """
    PLACEHOLDER.

    Future implementation will enumerate serial ports and identify an
    ESP32 dev board by known USB-to-UART bridge VID/PID pairs (e.g.
    CP2102, CH340) and/or by querying esptool for a chip ID.

    Returns:
        BoardInfo: currently always a "not connected" placeholder result.
    """
    logger.debug("detectESP32() called (placeholder - no implementation yet)")
    return BoardInfo(
        board_type=BOARD_ESP32,
        com_port="",
        description="Detection not yet implemented (Phase 1 placeholder)",
        is_connected=False,
    )


class BoardDetector:
    """
    PLACEHOLDER coordinating class.

    Intended to be the single object the GUI talks to for detection,
    regardless of which board family is currently selected. Wraps the
    free-function detectors above so the GUI does not need an if/else on
    board type.

    Future implementation should:
      - Run detection on a QThread / QRunnable so the UI never blocks.
      - Emit a Qt signal with the resulting BoardInfo (see
        ui/main_window.py for the signal/slot wiring pattern already used
        elsewhere in this project).
      - Support cancellation if the user changes board selection mid-scan.
    """

    def __init__(self):
        self._last_result: BoardInfo = BoardInfo(is_connected=False)

    def detect(self, board_type: str) -> BoardInfo:
        """
        Run detection for the given board type ('Arduino UNO/Nano' or
        'ESP32') and return the result. Currently delegates straight to
        the placeholder free functions above.
        """
        logger.info("BoardDetector.detect(%s) - placeholder", board_type)

        if board_type == BOARD_ARDUINO:
            result = detectArduino()
        elif board_type == BOARD_ESP32:
            result = detectESP32()
        else:
            logger.warning("Unknown board_type passed to detect(): %s", board_type)
            result = BoardInfo(board_type=board_type, is_connected=False)

        self._last_result = result
        return result

    @property
    def last_result(self) -> BoardInfo:
        return self._last_result

    @staticmethod
    def status_label(info: BoardInfo) -> str:
        """Convert a BoardInfo into the short status string the GUI shows."""
        if info.is_connected:
            return f"Detected on {info.com_port}"
        return STATUS_NOT_DETECTED
