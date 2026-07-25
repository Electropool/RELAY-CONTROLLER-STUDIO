"""
logger.py
================================================================================
Application-wide logging setup.

Provides a single get_logger() entry point that configures Python's
standard `logging` module to write to logs/app.log (rotating) as well as
the console (stdout), so that both a developer running from source and a
future frozen .exe get consistent diagnostic output.

The GUI's ConsolePanel widget attaches its own logging.Handler (see
ui/widgets/console_panel.py) so that everything logged through this module
also appears live in the on-screen console -- there is only one logging
pipeline, with multiple outputs.
================================================================================
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from core.constants import LOG_FILE, LOGS_DIR, APP_NAME

_LOGGER_NAME = "relay_controller_studio"
_configured = False


def _ensure_logs_dir() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure (once) and return the shared application logger.

    Safe to call multiple times -- only the first call actually attaches
    handlers, subsequent calls just return the existing logger.
    """
    global _configured

    logger = logging.getLogger(_LOGGER_NAME)

    if _configured:
        return logger

    _ensure_logs_dir()

    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler: keeps app.log from growing without bound.
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(LOG_FILE),
        maxBytes=2 * 1024 * 1024,  # 2 MB per file
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # Console handler: useful when running from a terminal during
    # development. The GUI's ConsolePanel adds its own separate handler.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("=" * 60)
    logger.info("%s logging initialized", APP_NAME)
    logger.info("Log file: %s", LOG_FILE)
    logger.info("=" * 60)

    _configured = True
    return logger


def get_logger() -> logging.Logger:
    """
    Return the shared application logger, configuring it on first use.
    Every module in the project should call this instead of instantiating
    its own logger, so that all output funnels through one file + one
    console + one GUI console panel.
    """
    return configure_logging()
