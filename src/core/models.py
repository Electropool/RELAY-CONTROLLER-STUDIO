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
class RelayEvent:
    """
    Configuration for a single timing event on a relay channel.
    """
    start_time: int = 0
    stop_time: int = 0
    enabled: bool = True
    oscillate: bool = False
    osc_period_ms: int = 1000

    def to_dict(self) -> dict:
        return {
            "start_time": self.start_time,
            "stop_time": self.stop_time,
            "enabled": self.enabled,
            "oscillate": self.oscillate,
            "osc_period_ms": self.osc_period_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RelayEvent:
        return cls(
            start_time=data.get("start_time", 0),
            stop_time=data.get("stop_time", 0),
            enabled=data.get("enabled", True),
            oscillate=data.get("oscillate", False),
            osc_period_ms=data.get("osc_period_ms", 1000),
        )


@dataclass(init=False)
class RelayObject:
    """
    Configuration for a single relay channel.
    Backward compatible API supports legacy fields `enabled`, `start_time`, `stop_time`.
    Internally stores a list of ``RelayEvent`` objects.
    """

    relay_number: int
    events: List[RelayEvent] = field(default_factory=list)

    def __init__(self, relay_number: int, enabled: bool = True, start_time: int = 0, stop_time: int = 0,
                 events: List[RelayEvent] = None, **kwargs):
        """Create a RelayObject.
        Supports the old signature (enabled, start_time, stop_time) and the newer ``events`` list.
        Extra kwargs are ignored for forward compatibility.
        """
        self.relay_number = relay_number
        if events is not None:
            self.events = events
        else:
            self.events = [RelayEvent(start_time=start_time, stop_time=stop_time, enabled=enabled)]
        # ignore any extra kwargs

    @property
    def enabled(self) -> bool:
        """True if any event is enabled (legacy: based on first event)."""
        return any(e.enabled for e in self.events) if self.events else False

    @enabled.setter
    def enabled(self, value: bool) -> None:
        if not self.events:
            self.events.append(RelayEvent())
        for e in self.events:
            e.enabled = value
        if not value and self.events:
            # When disabling, clear times of the first event for legacy behaviour
            self.events[0].start_time = 0
            self.events[0].stop_time = 0

    @property
    def start_time(self) -> int:
        """Legacy accessor for the start time of the first event."""
        return self.events[0].start_time if self.events else 0

    @start_time.setter
    def start_time(self, value: int) -> None:
        if not self.events:
            self.events.append(RelayEvent())
        self.events[0].start_time = value
        # Update enabled flag based on zero values
        self.events[0].enabled = not (self.events[0].start_time == 0 and self.events[0].stop_time == 0)

    @property
    def stop_time(self) -> int:
        """Legacy accessor for the stop time of the first event."""
        return self.events[0].stop_time if self.events else 0

    @stop_time.setter
    def stop_time(self, value: int) -> None:
        if not self.events:
            self.events.append(RelayEvent())
        self.events[0].stop_time = value
        self.events[0].enabled = not (self.events[0].start_time == 0 and self.events[0].stop_time == 0)

    @property
    def display_name(self) -> str:
        """Human‑readable channel label, e.g. 'Relay1'."""
        return f"Relay{self.relay_number + 1}"

    def to_dict(self) -> dict:
        return {
            "relay_number": self.relay_number,
            "events": [e.to_dict() for e in self.events],
            "enabled": self.events[0].enabled if self.events else True,
            "start_time": self.events[0].start_time if self.events else 0,
            "stop_time": self.events[0].stop_time if self.events else 0,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RelayObject":
        relay_number = data.get("relay_number", 0)
        if "events" in data:
            events = [RelayEvent.from_dict(e) for e in data["events"]]
        else:
            events = [RelayEvent(
                start_time=data.get("start_time", 0),
                stop_time=data.get("stop_time", 0),
                enabled=data.get("enabled", True),
                oscillate=False,
                osc_period_ms=1000,
            )]
        return cls(relay_number=relay_number, events=events)


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
            RelayObject(relay_number=i, events=[RelayEvent(start_time=0, stop_time=0, enabled=True, oscillate=False, osc_period_ms=1000)])
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

