"""
board_panel.py
================================================================================
BoardPanel: board selection, connection status, and the Refresh /
Upload Firmware action buttons.

Purely presentational -- it exposes Qt signals for user actions
(board changed, refresh requested, upload requested) and simple setter
methods for updating status text, and leaves all actual detection/upload
behavior to MainWindow + the core.* placeholder classes.
================================================================================
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.constants import STATUS_NOT_DETECTED, SUPPORTED_BOARDS


class BoardPanel(QGroupBox):
    """
    Signals:
        boardChanged(str): emitted when the user picks a different board
            from the dropdown.
        refreshRequested(): emitted when the Refresh button is clicked.
        uploadRequested(): emitted when the Upload Firmware button is
            clicked.
    """

    boardChanged = Signal(str)
    refreshRequested = Signal()
    uploadRequested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Board", parent)

        self.board_combo = QComboBox()
        self.board_combo.addItems(SUPPORTED_BOARDS)
        self.board_combo.currentTextChanged.connect(self.boardChanged.emit)

        self.status_label = QLabel(STATUS_NOT_DETECTED)
        self.status_label.setObjectName("boardStatusLabel")

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refreshRequested.emit)

        self.upload_button = QPushButton("Upload Firmware")
        self.upload_button.setObjectName("uploadButton")
        self.upload_button.clicked.connect(self.uploadRequested.emit)

        self._build_layout()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)

        combo_row = QHBoxLayout()
        combo_row.addWidget(QLabel("Board:"))
        combo_row.addWidget(self.board_combo, stretch=1)
        layout.addLayout(combo_row)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Status:"))
        status_row.addWidget(self.status_label, stretch=1)
        layout.addLayout(status_row)

        button_row = QHBoxLayout()
        button_row.addWidget(self.refresh_button)
        button_row.addWidget(self.upload_button)
        layout.addLayout(button_row)

    # ------------------------------------------------------------------
    def current_board(self) -> str:
        return self.board_combo.currentText()

    def set_status(self, text: str, is_connected: bool = False) -> None:
        self.status_label.setText(text)
        color = "#98c379" if is_connected else "#e06c75"
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 600;")

    def set_upload_enabled(self, enabled: bool) -> None:
        self.upload_button.setEnabled(enabled)
