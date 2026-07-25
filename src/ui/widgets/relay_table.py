"""
relay_table.py
================================================================================
RelayTableWidget: the dynamic relay configuration table.

Rebuilds its rows whenever the selected firmware's channel count changes
(2 / 4 / 8 / 16), showing one row per relay with:
    - Channel name (Relay1, Relay2, ...)
    - Enabled checkbox
    - Start Time (seconds)
    - Stop Time (seconds)

"Relay Active Low" is a single, firmware-wide setting (it applies to every
channel at once in the firmware), so it lives as one checkbox above the
table rather than as a per-row column -- see MainWindow / BoardPanel.

This widget only manages presentation and emits a Qt signal whenever the
user edits anything; it deliberately holds no upload/flashing logic itself
(GUI/logic separation).
================================================================================
"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHeaderView,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from core.logger import get_logger
from core.models import RelayObject

logger = get_logger()

COL_ENABLED = 0
COL_NAME = 1
COL_START = 2
COL_STOP = 3
COLUMN_HEADERS = ["Enabled", "Channel", "Start Time (s)", "Stop Time (s)"]

MAX_TIME_SECONDS = 24 * 60 * 60  # generous upper bound: 24 hours in seconds


class RelayTableWidget(QTableWidget):
    """
    A QTableWidget specialized for editing relay timing configuration.

    Signal:
        configChanged: emitted (with no payload) whenever any cell's value
            changes, so MainWindow can, e.g., re-enable an "Apply" button
            or refresh a preview. Kept payload-free/simple for Phase 1;
            callers should call get_channel_configs() to pull the latest
            state on demand.
    """

    configChanged = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setColumnCount(len(COLUMN_HEADERS))
        self.setHorizontalHeaderLabels(COLUMN_HEADERS)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.AllEditTriggers)

    # ------------------------------------------------------------------
    def set_channel_count(self, channel_count: int) -> None:
        """
        Rebuild the table with `channel_count` rows, each defaulted to
        enabled / start=0 / stop=0. Called whenever the firmware selector
        changes (e.g. 2CH -> 4CH).
        """
        logger.info("RelayTableWidget: rebuilding table for %s channels", channel_count)
        self.setRowCount(0)
        self.setRowCount(channel_count)

        for row in range(channel_count):
            self._build_row(row)

    def _build_row(self, row: int) -> None:
        # --- Enabled checkbox, centered via a small wrapper widget ------
        enabled_checkbox = QCheckBox()
        enabled_checkbox.setChecked(True)
        enabled_checkbox.stateChanged.connect(self.configChanged.emit)
        self.setCellWidget(row, COL_ENABLED, enabled_checkbox)

        # --- Channel name (read-only) ------------------------------------
        name_item = QTableWidgetItem(f"Relay{row + 1}")
        name_item.setFlags(name_item.flags() & ~Qt_ItemIsEditable())
        self.setItem(row, COL_NAME, name_item)

        # --- Start time spin box -----------------------------------------
        start_spin = QSpinBox()
        start_spin.setRange(0, MAX_TIME_SECONDS)
        start_spin.setValue(0)
        start_spin.valueChanged.connect(self.configChanged.emit)
        self.setCellWidget(row, COL_START, start_spin)

        # --- Stop time spin box --------------------------------------------
        stop_spin = QSpinBox()
        stop_spin.setRange(0, MAX_TIME_SECONDS)
        stop_spin.setValue(0)
        stop_spin.valueChanged.connect(self.configChanged.emit)
        self.setCellWidget(row, COL_STOP, stop_spin)

    # ------------------------------------------------------------------
    def get_channel_configs(self) -> List[RelayObject]:
        """Read the current table contents back out into model objects."""
        configs: List[RelayObject] = []
        for row in range(self.rowCount()):
            enabled_widget: QCheckBox = self.cellWidget(row, COL_ENABLED)  # type: ignore
            start_widget: QSpinBox = self.cellWidget(row, COL_START)  # type: ignore
            stop_widget: QSpinBox = self.cellWidget(row, COL_STOP)  # type: ignore

            configs.append(
                RelayObject(
                    relay_number=row,
                    enabled=enabled_widget.isChecked() if enabled_widget else True,
                    start_time=start_widget.value() if start_widget else 0,
                    stop_time=stop_widget.value() if stop_widget else 0,
                )
            )
        return configs

    def load_channel_configs(self, configs: List[RelayObject]) -> None:
        """Populate the table from a list of RelayObject."""
        self.blockSignals(True)
        self.set_channel_count(len(configs))
        for row, cfg in enumerate(configs):
            enabled_widget: QCheckBox = self.cellWidget(row, COL_ENABLED)  # type: ignore
            start_widget: QSpinBox = self.cellWidget(row, COL_START)  # type: ignore
            stop_widget: QSpinBox = self.cellWidget(row, COL_STOP)  # type: ignore

            if enabled_widget:
                enabled_widget.blockSignals(True)
                enabled_widget.setChecked(cfg.enabled)
                enabled_widget.blockSignals(False)
            if start_widget:
                start_widget.blockSignals(True)
                start_widget.setValue(cfg.start_time)
                start_widget.blockSignals(False)
            if stop_widget:
                stop_widget.blockSignals(True)
                stop_widget.setValue(cfg.stop_time)
                stop_widget.blockSignals(False)
        self.blockSignals(False)

    # ------------------------------------------------------------------
    # Validation Feedback
    # ------------------------------------------------------------------
    def set_field_error(self, row: int, field_type: str, message: str) -> None:
        col = COL_START if field_type == "start" else COL_STOP
        widget = self.cellWidget(row, col)
        if widget:
            widget.setStyleSheet("border: 2px solid red;")
            widget.setToolTip(message)

    def clear_field_errors(self) -> None:
        for row in range(self.rowCount()):
            for col in (COL_START, COL_STOP):
                widget = self.cellWidget(row, col)
                if widget:
                    widget.setStyleSheet("")
                    widget.setToolTip("")

def Qt_ItemIsEditable():
    """
    Small indirection so this file only needs a single top-level Qt.*
    import site if Qt's flag enum location changes between PySide6
    minor versions. Kept as a function rather than a bare import to make
    the intent ("we deliberately disable editing of this one column")
    self-documenting at the call site above.
    """
    from PySide6.QtCore import Qt

    return Qt.ItemIsEditable
