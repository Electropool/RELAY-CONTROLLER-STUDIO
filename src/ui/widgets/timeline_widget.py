"""
timeline_widget.py
================================================================================
TimelineWidget: A custom graphical timeline preview displaying relay channel
activation schedules as scaled horizontal bars.
================================================================================
"""

from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from core.models import RelayConfiguration


class TimelineWidget(QWidget):
    """
    Renders a graphical timeline preview of active relay channels.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.config: Optional[RelayConfiguration] = None
        self.setMinimumHeight(140)
        self.setStyleSheet("background-color: #1e2024; border: 1px solid #3a3d41; border-radius: 4px;")

    def set_configuration(self, config: RelayConfiguration) -> None:
        self.config = config
        self.update()  # Trigger repaint

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        if not self.config or not self.config.relay_list:
            painter.setPen(QPen(QColor("#abb2bf")))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Relay Configuration Available")
            return

        loop_time = max(1, self.config.loop_time)
        relays = self.config.relay_list
        count = len(relays)

        # Margins & Dimensions
        left_margin = 80
        right_margin = 20
        top_margin = 30
        bottom_margin = 25

        timeline_w = max(10, w - left_margin - right_margin)
        timeline_h = max(10, h - top_margin - bottom_margin)

        # Draw Time Scale Header
        painter.setPen(QPen(QColor("#5c6370"), 1, Qt.DashLine))
        font = QFont("Consolas", 8)
        painter.setFont(font)

        divisions = 5
        for i in range(divisions + 1):
            ratio = i / divisions
            x = left_margin + ratio * timeline_w
            time_val = int(ratio * loop_time)
            
            # Grid line
            painter.drawLine(int(x), top_margin - 5, int(x), h - bottom_margin + 5)

            # Time text label
            painter.setPen(QPen(QColor("#abb2bf")))
            painter.drawText(
                QRectF(x - 25, 5, 50, 20),
                Qt.AlignCenter,
                f"{time_val}s",
            )
            painter.setPen(QPen(QColor("#5c6370"), 1, Qt.DashLine))

        # Row Heights
        row_h = timeline_h / count
        bar_h = max(6, min(24, row_h * 0.65))

        for idx, r in enumerate(relays):
            y_center = top_margin + (idx + 0.5) * row_h
            bar_y = y_center - bar_h / 2

            # Channel Label
            painter.setPen(QPen(QColor("#61afef") if r.enabled else QColor("#5c6370")))
            lbl_font = QFont("Segoe UI", 9, QFont.Bold if r.enabled else QFont.Normal)
            painter.setFont(lbl_font)
            painter.drawText(
                QRectF(5, bar_y, left_margin - 12, bar_h),
                Qt.AlignRight | Qt.AlignVCenter,
                f"Relay {r.relay_number + 1}",
            )

            # Lane background track
            track_rect = QRectF(left_margin, bar_y, timeline_w, bar_h)
            painter.setBrush(QColor("#16171a"))
            painter.setPen(QPen(QColor("#2c313a"), 1))
            painter.drawRoundedRect(track_rect, 3, 3)

            is_disabled = (not r.enabled) or (r.start_time == 0 and r.stop_time == 0)

            if is_disabled:
                # Greyed out bar
                painter.setBrush(QColor("#21252b"))
                painter.setPen(QPen(QColor("#3a3d41"), 1))
                painter.drawRoundedRect(track_rect, 3, 3)

                painter.setPen(QPen(QColor("#5c6370")))
                small_font = QFont("Segoe UI", 7)
                painter.setFont(small_font)
                painter.drawText(track_rect, Qt.AlignCenter, "OFF / Disabled")
            else:
                # Active timing bar
                start_x = left_margin + (min(r.start_time, loop_time) / loop_time) * timeline_w
                stop_x = left_margin + (min(r.stop_time, loop_time) / loop_time) * timeline_w
                bar_w = max(2.0, stop_x - start_x)

                active_rect = QRectF(start_x, bar_y, bar_w, bar_h)

                # Gradient fill
                grad = QLinearGradient(active_rect.topLeft(), active_rect.topRight())
                grad.setColorAt(0.0, QColor("#98c379"))  # Soft green
                grad.setColorAt(1.0, QColor("#61afef"))  # Soft blue

                painter.setBrush(grad)
                painter.setPen(QPen(QColor("#98c379"), 1))
                painter.drawRoundedRect(active_rect, 3, 3)

                # Time duration text inside active bar
                if bar_w > 45:
                    painter.setPen(QPen(QColor("#1e2024")))
                    val_font = QFont("Consolas", 8, QFont.Bold)
                    painter.setFont(val_font)
                    painter.drawText(
                        active_rect,
                        Qt.AlignCenter,
                        f"{r.start_time}s - {r.stop_time}s",
                    )
