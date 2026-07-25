"""
board_detector.py
================================================================================
Detects connected microcontrollers (Arduino UNO, Arduino Nano, ESP32)
by enumerating serial ports and matching USB Vendor/Product IDs (VID/PID) and
manufacturer/product description strings.
================================================================================
"""

from __future__ import annotations

import serial.tools.list_ports
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
    Enumerate serial ports and identify an Arduino UNO/Nano by USB VID/PID pairs
    or description matches.
    """
    try:
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            vid = port.vid or 0
            pid = port.pid or 0
            desc = (port.description or "").lower()
            mfg = (port.manufacturer or "").lower()

            # Genuine Arduino / FTDI / CH340 commonly used in UNO/Nano
            is_arduino_vid = vid in (0x2341, 0x2A03, 0x0403)
            is_ch340 = vid == 0x1A86 and pid == 0x7523
            is_arduino_desc = any(x in desc or x in mfg for x in ("arduino", "uno", "nano", "ft232", "ch340"))

            if is_arduino_vid or is_ch340 or is_arduino_desc:
                name = "Arduino UNO/Nano"
                if "nano" in desc or vid == 0x0403:
                    name = "Arduino Nano"
                elif "uno" in desc or vid == 0x2341:
                    name = "Arduino UNO"
                
                logger.info("Detected %s on %s", name, port.device)
                return BoardInfo(
                    board_type=BOARD_ARDUINO,
                    com_port=port.device,
                    description=f"{name} ({port.description})",
                    is_connected=True,
                )
    except Exception as e:
        logger.error("Error detecting Arduino board: %s", e)

    return BoardInfo(
        board_type=BOARD_ARDUINO,
        com_port="",
        description="No Arduino UNO/Nano detected",
        is_connected=False,
    )


def detectESP32() -> BoardInfo:
    """
    Enumerate serial ports and identify an ESP32 dev board by USB-to-UART bridge
    VID/PID pairs and/or description matches.
    """
    try:
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            vid = port.vid or 0
            pid = port.pid or 0
            desc = (port.description or "").lower()
            mfg = (port.manufacturer or "").lower()

            # CP210x / CH340 / CH9102 commonly used on ESP32 dev boards
            is_esp32_vid = vid in (0x10C4, 0x1A86)
            is_esp32_desc = any(x in desc or x in mfg for x in ("esp32", "cp210", "nodemcu", "silicon labs", "uart", "ch9102"))

            if is_esp32_vid or is_esp32_desc:
                logger.info("Detected ESP32 on %s", port.device)
                return BoardInfo(
                    board_type=BOARD_ESP32,
                    com_port=port.device,
                    description=f"ESP32 Dev Module ({port.description})",
                    is_connected=True,
                )
    except Exception as e:
        logger.error("Error detecting ESP32 board: %s", e)

    return BoardInfo(
        board_type=BOARD_ESP32,
        com_port="",
        description="No ESP32 detected",
        is_connected=False,
    )


class BoardDetector:
    """
    Coordinating class that the GUI talks to for board detection.
    """

    def __init__(self):
        self._last_result: BoardInfo = BoardInfo(is_connected=False)

    def detect(self, board_type: str) -> BoardInfo:
        """
        Run detection for the given board type and return the result.
        """
        logger.info("BoardDetector.detect(%s) initiated", board_type)

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
