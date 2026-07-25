"""
firmware_panel.py
================================================================================
FirmwarePanel: firmware (channel count) selection, loop/cycle time, and the
firmware-wide "Relay Active Low" polarity checkbox.

Channel choices are populated dynamically from FirmwareCatalog so the
dropdown always reflects what firmware actually exists on disk under
firmware/<BOARD>/<N>CH/, rather than a hard-coded list that could go stale.
================================================================================
"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.constants import DEFAULT_TOTAL_TIME_SECONDS


class FirmwarePanel(QGroupBox):
    """
    Signals:
        channelCountChanged(int): emitted when the user selects a
            different relay-channel firmware build (2 / 4 / 8 / 16).
        loopTimeChanged(int): emitted when the loop/cycle time spin box
            changes.
        activeLowChanged(bool): emitted when the polarity checkbox toggles.
    """

    channelCountChanged = Signal(int)
    loopTimeChanged = Signal(int)
    activeLowChanged = Signal(bool)
    brightnessChanged = Signal(int)
    countdownChanged = Signal(bool)

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Firmware", parent)

        self.channel_combo = QComboBox()
        self.channel_combo.currentTextChanged.connect(self._on_channel_changed)

        self.loop_time_spin = QSpinBox()
        self.loop_time_spin.setRange(1, 24 * 60 * 60)
        self.loop_time_spin.setSuffix(" s")
        self.loop_time_spin.setValue(DEFAULT_TOTAL_TIME_SECONDS)
        self.loop_time_spin.valueChanged.connect(self.loopTimeChanged.emit)

        self.brightness_spin = QSpinBox()
        self.brightness_spin.setRange(0, 15) # Assuming typical 0-15 or 0-7. TM1637 max is 7, maybe 15 for 8-bit? Let's use 0 to 15.
        self.brightness_spin.setValue(7)
        self.brightness_spin.valueChanged.connect(self.brightnessChanged.emit)

        self.countdown_checkbox = QCheckBox("Countdown Enable")
        self.countdown_checkbox.setChecked(True)
        self.countdown_checkbox.toggled.connect(self.countdownChanged.emit)

        self.active_low_checkbox = QCheckBox("Relay Active Low")
        self.active_low_checkbox.setChecked(True)
        self.active_low_checkbox.toggled.connect(self.activeLowChanged.emit)

        self._build_layout()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)

        channel_row = QHBoxLayout()
        channel_row.addWidget(QLabel("Relay Count:"))
        channel_row.addWidget(self.channel_combo, stretch=1)
        layout.addLayout(channel_row)

        loop_row = QHBoxLayout()
        loop_row.addWidget(QLabel("Loop Time:"))
        loop_row.addWidget(self.loop_time_spin, stretch=1)
        layout.addLayout(loop_row)

        brightness_row = QHBoxLayout()
        brightness_row.addWidget(QLabel("Brightness:"))
        brightness_row.addWidget(self.brightness_spin, stretch=1)
        layout.addLayout(brightness_row)

        layout.addWidget(self.countdown_checkbox)
        layout.addWidget(self.active_low_checkbox)

    # ------------------------------------------------------------------
    def set_available_channel_counts(self, counts: List[int]) -> None:
        """Repopulate the dropdown, e.g. after the board selection changes
        and a different set of firmware folders becomes relevant."""
        self.channel_combo.blockSignals(True)
        self.channel_combo.clear()
        for count in counts:
            self.channel_combo.addItem(f"{count} Relay", userData=count)
        self.channel_combo.blockSignals(False)

        if counts:
            self.channel_combo.setCurrentIndex(0)
            self.channelCountChanged.emit(counts[0])

    def _on_channel_changed(self, _text: str) -> None:
        count = self.channel_combo.currentData()
        if count is not None:
            self.channelCountChanged.emit(count)

    def current_channel_count(self) -> int:
        return self.channel_combo.currentData() or 0

    def current_loop_time(self) -> int:
        return self.loop_time_spin.value()

    def current_brightness(self) -> int:
        return self.brightness_spin.value()

    def is_countdown_enabled(self) -> bool:
        return self.countdown_checkbox.isChecked()

    def is_active_low(self) -> bool:
        return self.active_low_checkbox.isChecked()

    # ------------------------------------------------------------------
    # Data Sync (Model -> GUI)
    # ------------------------------------------------------------------
    def set_loop_time(self, seconds: int) -> None:
        self.loop_time_spin.blockSignals(True)
        self.loop_time_spin.setValue(seconds)
        self.loop_time_spin.blockSignals(False)

    def set_brightness(self, value: int) -> None:
        self.brightness_spin.blockSignals(True)
        self.brightness_spin.setValue(value)
        self.brightness_spin.blockSignals(False)

    def set_countdown_enabled(self, enabled: bool) -> None:
        self.countdown_checkbox.blockSignals(True)
        self.countdown_checkbox.setChecked(enabled)
        self.countdown_checkbox.blockSignals(False)

    def set_active_low(self, enabled: bool) -> None:
        self.active_low_checkbox.blockSignals(True)
        self.active_low_checkbox.setChecked(enabled)
        self.active_low_checkbox.blockSignals(False)

    def set_current_channel_count(self, count: int) -> None:
        index = self.channel_combo.findData(count)
        if index >= 0:
            self.channel_combo.blockSignals(True)
            self.channel_combo.setCurrentIndex(index)
            self.channel_combo.blockSignals(False)

    # ------------------------------------------------------------------
    # Validation Feedback
    # ------------------------------------------------------------------
    def set_field_error(self, field_name: str, message: str) -> None:
        if field_name == "loop_time":
            self.loop_time_spin.setStyleSheet("border: 2px solid red;")
            self.loop_time_spin.setToolTip(message)
            
    def clear_field_errors(self) -> None:
        self.loop_time_spin.setStyleSheet("")
        self.loop_time_spin.setToolTip("")

