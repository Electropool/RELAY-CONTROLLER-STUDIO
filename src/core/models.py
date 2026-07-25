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


import json


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

    def to_dict(self) -> dict:
        return {
            "relay_number": self.relay_number,
            "enabled": self.enabled,
            "start_time": self.start_time,
            "stop_time": self.stop_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RelayObject:
        return cls(
            relay_number=data.get("relay_number", 0),
            enabled=data.get("enabled", True),
            start_time=data.get("start_time", 0),
            stop_time=data.get("stop_time", 0),
        )


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

    def to_dict(self) -> dict:
        return {
            "board_type": self.board_type,
            "firmware_type": self.firmware_type,
            "loop_time": self.loop_time,
            "relay_active_low": self.relay_active_low,
            "display_brightness": self.display_brightness,
            "countdown_enable": self.countdown_enable,
            "relay_list": [r.to_dict() for r in self.relay_list],
        }

    @classmethod
    def from_dict(cls, data: dict) -> RelayConfiguration:
        relay_list = [
            RelayObject.from_dict(r)
            for r in data.get("relay_list", [])
        ]
        return cls(
            board_type=data.get("board_type", "Arduino UNO"),
            firmware_type=data.get("firmware_type", len(relay_list) or 2),
            loop_time=data.get("loop_time", DEFAULT_TOTAL_TIME_SECONDS),
            relay_active_low=data.get("relay_active_low", DEFAULT_RELAY_ACTIVE_LOW),
            display_brightness=data.get("display_brightness", 7),
            countdown_enable=data.get("countdown_enable", True),
            relay_list=relay_list,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> RelayConfiguration:
        return cls.from_dict(json.loads(json_str))


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

