"""
models.py
================================================================================
Plain data classes describing the state the GUI edits and the (future)
firmware-writing / upload layers will consume.

These are intentionally "dumb" containers with no Qt dependency at all --
that keeps them reusable from unit tests, from the CLI (if one is added
later), and from the GUI, and keeps the GUI <-> logic separation clean.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from core.constants import DEFAULT_RELAY_ACTIVE_LOW, DEFAULT_TOTAL_TIME_SECONDS


@dataclass
class RelayObject:
    """
    Configuration for a single relay channel.

    Attributes:
        relay_number: Zero-based channel index (0 == "Relay1").
        enabled: Is the relay enabled.
        start_time: Seconds from the start of the cycle.
        stop_time: Seconds from the start of the cycle.
    """

    relay_number: int
    enabled: bool = True
    start_time: int = 0
    stop_time: int = 0

    @property
    def display_name(self) -> str:
        """Human-readable channel label, e.g. 'Relay1'."""
        return f"Relay{self.relay_number + 1}"


@dataclass
class RelayConfiguration:
    """
    Single source of truth for the GUI state.
    """

    board_type: str
    firmware_type: int
    loop_time: int = DEFAULT_TOTAL_TIME_SECONDS
    relay_active_low: bool = DEFAULT_RELAY_ACTIVE_LOW
    display_brightness: int = 7
    countdown_enable: bool = True
    relay_list: List[RelayObject] = field(default_factory=list)

    @staticmethod
    def create_default(board: str, channel_count: int) -> "RelayConfiguration":
        """
        Build a fresh configuration for the given board/channel selection.
        """
        relays = [
            RelayObject(relay_number=i)
            for i in range(channel_count)
        ]
        return RelayConfiguration(
            board_type=board,
            firmware_type=channel_count,
            loop_time=DEFAULT_TOTAL_TIME_SECONDS,
            relay_active_low=DEFAULT_RELAY_ACTIVE_LOW,
            display_brightness=7,
            countdown_enable=True,
            relay_list=relays,
        )


@dataclass
class BoardInfo:
    """
    Describes a detected (or manually selected) hardware board. Populated
    by BoardDetector implementations in a future phase; only the shape of
    the data is defined here.
    """

    board_type: str = ""
    com_port: str = ""
    description: str = ""
    is_connected: bool = False
