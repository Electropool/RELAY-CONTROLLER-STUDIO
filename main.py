#!/usr/bin/env python3
"""
main.py
================================================================================
Application entry point for Relay Controller Studio.

Responsibilities of this file, and ONLY this file:
    1. Make src/ importable (so internal modules use clean absolute
       imports like `from core.logger import get_logger` instead of
       fragile relative imports).
    2. Initialize logging.
    3. Construct the QApplication, load the theme stylesheet, and show
       the MainWindow.

All actual application logic lives under src/core/ and src/ui/ -- this
file deliberately contains no business logic of its own.

Run with:
    python main.py
or via the provided run.bat on Windows.
================================================================================
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make the src/ directory importable as top-level packages (core, ui) both
# when running from source AND when frozen with PyInstaller. See build.bat
# / README.md "Building a Windows executable" for how PyInstaller handles
# this path at freeze time.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtGui import QIcon  # noqa: E402  (after sys.path setup)
from PySide6.QtWidgets import QApplication, QDialog  # noqa: E402

from core.constants import ASSETS_DIR, ICONS_DIR, APP_NAME, APP_ORG  # noqa: E402
from core.logger import get_logger  # noqa: E402


def _load_stylesheet(app: QApplication) -> None:
    """Load the default theme .qss file, if present. Falls back to the
    platform-default Qt look silently if the file is missing, so a
    stripped-down build never crashes just because assets/ is absent."""
    qss_path = SRC_DIR / "ui" / "resources" / "theme.qss"
    if qss_path.is_file():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    else:
        logger = get_logger()
        logger.warning("Stylesheet not found at %s -- using default Qt style.", qss_path)


def main() -> int:
    logger = get_logger()
    logger.info("Starting %s...", APP_NAME)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)

    # Set the application-wide icon (window title bar, taskbar, Alt+Tab)
    icon_path = ICONS_DIR / "icon.png"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        logger.warning("Application icon not found at %s", icon_path)

    _load_stylesheet(app)

    # Check if first startup has completed
    from core.settings_manager import SettingsManager
    settings_mgr = SettingsManager()
    
    # Check if tools are ready. If not completed, show setup wizard
    if not settings_mgr.settings.first_startup_complete:
        from ui.widgets.startup_wizard import StartupWizardDialog
        wizard = StartupWizardDialog(settings_mgr)
        # Apply stylesheet to wizard dialog
        qss_path = Path(__file__).resolve().parent / "src" / "ui" / "resources" / "theme.qss"
        if qss_path.is_file():
            wizard.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        
        if wizard.exec() != QDialog.DialogCode.Accepted:
            logger.info("Setup wizard not completed. Exiting.")
            return 0

    # Imported here (after sys.path setup) rather than at module top, so
    # `python main.py` and a frozen PyInstaller build resolve `ui.*` the
    # same way.
    from ui.main_window import MainWindow  # noqa: E402

    window = MainWindow()
    window.show()

    logger.info("Main window shown, entering Qt event loop.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
