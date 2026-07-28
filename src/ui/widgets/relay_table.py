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
from core.models import RelayObject, RelayEvent

logger = get_logger()

COL_ENABLED = 0
COL_NAME = 1
COL_START = 2
COL_STOP = 3
COL_OSCILLATE = 4
COL_OSC_PERIOD = 5
COLUMN_HEADERS = ["Enabled", "Channel", "Start Time (s)", "Stop Time (s)", "Oscillate", "Oscillation Period (ms)"]

MAX_TIME_SECONDS = 24 * 60 * 60  # generous upper bound: 24 hours in seconds


class RelayTableWidget(QTableWidget):
    """
    A QTableWidget specialized for editing relay timing configurations with multiple events.
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
        self._configs: List[RelayObject] = []
        self._row_mapping = []  # List of (RelayObject, event_index)

    def set_channel_count(self, channel_count: int) -> None:
        """Rebuild the table for a fresh layout."""
        # Note: MainWindow handles syncing configuration model and then calling load_channel_configs
        pass

    def _build_row(self, row: int, cfg: RelayObject, event_idx: int, event: RelayEvent) -> None:
        # --- Enabled checkbox ------
        enabled_checkbox = QCheckBox()
        enabled_checkbox.setChecked(event.enabled)
        enabled_checkbox.stateChanged.connect(self._on_widget_changed)
        self.setCellWidget(row, COL_ENABLED, enabled_checkbox)

        # --- Channel name (read-only) ------
        name_str = f"Relay {cfg.relay_number + 1} - Event {event_idx + 1}"
        if event.start_time == 0 and event.stop_time == 0:
            name_str += " (Add Event...)"
        name_item = QTableWidgetItem(name_str)
        name_item.setFlags(name_item.flags() & ~Qt_ItemIsEditable())
        self.setItem(row, COL_NAME, name_item)

        # --- Start time spin box ------
        start_spin = QSpinBox()
        start_spin.setRange(0, MAX_TIME_SECONDS)
        start_spin.setValue(event.start_time)
        start_spin.valueChanged.connect(self._on_widget_changed)
        start_spin.editingFinished.connect(self._cleanup_and_sync_table)
        self.setCellWidget(row, COL_START, start_spin)

        # --- Stop time spin box ------
        stop_spin = QSpinBox()
        stop_spin.setRange(0, MAX_TIME_SECONDS)
        stop_spin.setValue(event.stop_time)
        stop_spin.valueChanged.connect(self._on_widget_changed)
        stop_spin.editingFinished.connect(self._cleanup_and_sync_table)
        self.setCellWidget(row, COL_STOP, stop_spin)

        # --- Oscillate checkbox ------
        osc_checkbox = QCheckBox()
        osc_checkbox.setChecked(event.oscillate)
        osc_checkbox.stateChanged.connect(self._on_widget_changed)
        self.setCellWidget(row, COL_OSCILLATE, osc_checkbox)

        # --- Oscillation Period (ms) ------
        osc_period_spin = QSpinBox()
        osc_period_spin.setRange(10, 1000000)
        osc_period_spin.setSingleStep(100)
        osc_period_spin.setValue(event.osc_period_ms)
        osc_period_spin.valueChanged.connect(self._on_widget_changed)
        osc_period_spin.editingFinished.connect(self._cleanup_and_sync_table)
        self.setCellWidget(row, COL_OSC_PERIOD, osc_period_spin)

        # Set visibility / state of oscillation period
        osc_period_spin.setEnabled(event.oscillate)
        osc_period_spin.setVisible(event.oscillate)

    def _on_widget_changed(self) -> None:
        sender_widget = self.sender()
        if not sender_widget:
            return
        pos = sender_widget.mapToParent(sender_widget.rect().center())
        index = self.indexAt(pos)
        if index.isValid():
            self._on_cell_changed(index.row())

    def _on_cell_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._row_mapping):
            return
        cfg, event_idx = self._row_mapping[row]
        event = cfg.events[event_idx]

        enabled_widget: QCheckBox = self.cellWidget(row, COL_ENABLED)  # type: ignore
        start_widget: QSpinBox = self.cellWidget(row, COL_START)  # type: ignore
        stop_widget: QSpinBox = self.cellWidget(row, COL_STOP)  # type: ignore
        osc_widget: QCheckBox = self.cellWidget(row, COL_OSCILLATE)  # type: ignore
        osc_period_widget: QSpinBox = self.cellWidget(row, COL_OSC_PERIOD)  # type: ignore

        old_empty = (event.start_time == 0 and event.stop_time == 0)
        old_osc = event.oscillate
        old_period = event.osc_period_ms

        new_enabled = enabled_widget.isChecked() if enabled_widget else True
        new_start = start_widget.value() if start_widget else 0
        new_stop = stop_widget.value() if stop_widget else 0
        new_osc = osc_widget.isChecked() if osc_widget else False
        new_period = osc_period_widget.value() if osc_period_widget else 1000

        event.enabled = new_enabled
        event.start_time = new_start
        event.stop_time = new_stop
        event.oscillate = new_osc
        event.osc_period_ms = new_period

        if osc_period_widget:
            osc_period_widget.setEnabled(new_osc)
            osc_period_widget.setVisible(new_osc)

        # Logging transition states
        new_empty = (new_start == 0 and new_stop == 0)
        if old_empty and not new_empty:
            logger.info("Event Added")
        elif not old_empty and new_empty:
            logger.info("Event Removed")

        if old_osc != new_osc:
            if new_osc:
                logger.info("Oscillation Enabled")
            else:
                logger.info("Oscillation Disabled")

        if old_period != new_period:
            logger.info("Oscillation Period Changed to %d ms", new_period)

        # Auto add empty event row if needed
        if old_empty and not new_empty:
            cfg.events.append(RelayEvent(start_time=0, stop_time=0, enabled=True, oscillate=False, osc_period_ms=1000))
            self.load_channel_configs(self._configs)
            # Restore focus to edited spinbox
            new_widget = self.cellWidget(row, COL_START)
            if new_widget:
                new_widget.setFocus()

        self.configChanged.emit()

    def _cleanup_and_sync_table(self) -> None:
        needed_rebuild = False
        for cfg in self._configs:
            non_empty = [e for e in cfg.events if not (e.start_time == 0 and e.stop_time == 0)]
            non_empty.append(RelayEvent(start_time=0, stop_time=0, enabled=True, oscillate=False, osc_period_ms=1000))
            if len(non_empty) != len(cfg.events):
                cfg.events = non_empty
                needed_rebuild = True

        if needed_rebuild:
            self.load_channel_configs(self._configs)
            self.configChanged.emit()

    def get_channel_configs(self) -> List[RelayObject]:
        """Read the current configs list."""
        return self._configs

    def load_channel_configs(self, configs: List[RelayObject]) -> None:
        """Populate the table from a list of RelayObject."""
        self.blockSignals(True)
        self._configs = configs
        
        # Ensure exactly one empty event at the end for each relay
        for cfg in self._configs:
            non_empty = [e for e in cfg.events if not (e.start_time == 0 and e.stop_time == 0)]
            non_empty.append(RelayEvent(start_time=0, stop_time=0, enabled=True, oscillate=False, osc_period_ms=1000))
            cfg.events = non_empty

        total_rows = sum(len(cfg.events) for cfg in self._configs)
        self.setRowCount(total_rows)

        row_idx = 0
        self._row_mapping = []
        for cfg in self._configs:
            for event_idx, event in enumerate(cfg.events):
                self._row_mapping.append((cfg, event_idx))
                self._build_row(row_idx, cfg, event_idx, event)
                row_idx += 1
        self.blockSignals(False)

    # ------------------------------------------------------------------
    # Validation Feedback
    # ------------------------------------------------------------------
    def set_field_error(self, relay_idx: int, event_idx: int, field_type: str, message: str) -> None:
        target_row = -1
        for row, (cfg, ev_idx) in enumerate(self._row_mapping):
            if cfg.relay_number == relay_idx and ev_idx == event_idx:
                target_row = row
                break

        if target_row != -1:
            if field_type == "start":
                col = COL_START
            elif field_type == "stop":
                col = COL_STOP
            elif field_type == "osc_period":
                col = COL_OSC_PERIOD
            else:
                return

            widget = self.cellWidget(target_row, col)
            if widget:
                widget.setStyleSheet("border: 2px solid red;")
                widget.setToolTip(message)

    def clear_field_errors(self) -> None:
        for row in range(self.rowCount()):
            for col in (COL_START, COL_STOP, COL_OSC_PERIOD):
                widget = self.cellWidget(row, col)
                if widget:
                    widget.setStyleSheet("")
                    widget.setToolTip("")


def Qt_ItemIsEditable():
    from PySide6.QtCore import Qt
    return Qt.ItemIsEditable
