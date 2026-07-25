"""
validation_panel.py
================================================================================
ValidationSummaryPanel: displays a summary of validation errors.
================================================================================
"""

from __future__ import annotations

from typing import List

from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from core.validation_manager import ValidationError

class ValidationSummaryPanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None):
        super().__init__("Validation Summary", parent)
        
        self.status_label = QLabel("✔ Configuration Valid")
        self.status_label.setStyleSheet("color: #98c379; font-weight: 600;")
        
        self.errors_layout = QVBoxLayout()
        self.errors_widget = QWidget()
        self.errors_widget.setLayout(self.errors_layout)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.errors_widget)
        
    def set_errors(self, errors: List[ValidationError]) -> None:
        # Clear existing errors
        while self.errors_layout.count():
            item = self.errors_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if not errors:
            self.status_label.setText("✔ Configuration Valid")
            self.status_label.setStyleSheet("color: #98c379; font-weight: 600;")
        else:
            self.status_label.setText(f"✖ {len(errors)} Errors Found")
            self.status_label.setStyleSheet("color: #e06c75; font-weight: 600;")
            for error in errors:
                err_label = QLabel(f"• {error.message}")
                err_label.setStyleSheet("color: #e06c75;")
                self.errors_layout.addWidget(err_label)
