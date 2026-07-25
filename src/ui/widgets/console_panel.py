"""
console_panel.py
================================================================================
ConsolePanel: the built-in, read-only console/log view shown at the bottom
of the main window.

It is a genuinely working piece of infrastructure (not a placeholder): it
attaches a logging.Handler to the shared application logger (see
core/logger.py) so that ANY module in the app -- board detection, upload
placeholders, settings, etc. -- can just call logger.info(...) and have the
message show up here automatically, color-coded by level, with zero
knowledge of the GUI layer. This is what keeps GUI and logic separated:
logic code never imports Qt or touches this widget directly.
================================================================================
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QWidget

LEVEL_COLORS = {
    logging.DEBUG: "#888888",
    logging.INFO: "#d4d4d4",
    logging.WARNING: "#e5c07b",
    logging.ERROR: "#e06c75",
    logging.CRITICAL: "#ff5555",
}


class _QtLogSignalEmitter(QObject):
    """
    Tiny QObject whose only job is to own a Signal.

    logging.Handler.emit() can be called from any thread (e.g. a future
    background upload/detection QThread). Qt widgets may only be touched
    from the GUI thread, so the handler below emits a Qt signal instead of
    writing to the QPlainTextEdit directly; Qt's queued connection
    machinery marshals that back onto the GUI thread safely.
    """

    message_logged = Signal(str, int)  # (formatted message, levelno)


class QtLogHandler(logging.Handler):
    """A logging.Handler that forwards records to the console widget via
    a thread-safe Qt signal instead of touching widgets directly."""

    def __init__(self):
        super().__init__()
        self.emitter = _QtLogSignalEmitter()
        self.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                                             datefmt="%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            self.emitter.message_logged.emit(message, record.levelno)
        except Exception:
            # Logging must never crash the application it's logging for.
            self.handleError(record)


class ConsolePanel(QPlainTextEdit):
    """
    Read-only, monospace, dark-themed console output panel.

    Intended future content (per project requirements): board detection
    results, compilation output, upload progress, errors/warnings/success
    messages -- all of which simply flow in via the standard `logging`
    module once a module calls core.logger.get_logger().
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(5000)  # cap memory usage on long sessions
        self.setObjectName("consolePanel")
        self.setPlaceholderText("Console output will appear here...")

        self._handler = QtLogHandler()
        self._handler.emitter.message_logged.connect(self._append_message)

    def attach_to_logger(self, logger: logging.Logger) -> None:
        """Attach this panel's handler to the given logger so every future
        log call is mirrored into the on-screen console."""
        logger.addHandler(self._handler)

    def _append_message(self, message: str, levelno: int) -> None:
        color = LEVEL_COLORS.get(levelno, "#d4d4d4")
        self.appendHtml(f'<span style="color:{color};">{_escape(message)}</span>')
        self.moveCursor(QTextCursor.End)

    def clear_console(self) -> None:
        self.clear()


def _escape(text: str) -> str:
    """Minimal HTML escaping so log messages containing '<' or '&' don't
    get interpreted as markup inside appendHtml()."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
