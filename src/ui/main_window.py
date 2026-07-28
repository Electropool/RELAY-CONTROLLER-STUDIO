"""
main_window.py
================================================================================
MainWindow: assembles every widget in ui/widgets/ into the application's
single top-level window, wires signals to core modules, and manages project
file persistence, undo/redo state, crash recovery, background flashing,
timeline previews, and update checks.
================================================================================
"""

from __future__ import annotations

import os
from typing import Optional, List
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from core.board_detector import BoardDetector
from core.constants import (
    APP_NAME,
    APP_VERSION,
    STATUS_DETECTING,
    BOARD_ARDUINO,
    CRASH_RECOVERY_FILE,
    ICONS_DIR,
)
from core.firmware_manager import FirmwareCatalog, FirmwareConfigurator
from core.logger import get_logger
from core.models import RelayConfiguration, RelayObject
from core.settings_manager import SettingsManager
from core.uploader import ArduinoUploader, ESP32Uploader, UploadWorkerThread
from core.validation_manager import ValidationManager
from core.update_checker import check_for_updates

from ui.widgets.board_panel import BoardPanel
from ui.widgets.console_panel import ConsolePanel
from ui.widgets.firmware_panel import FirmwarePanel
from ui.widgets.relay_table import RelayTableWidget
from ui.widgets.timeline_widget import TimelineWidget
from ui.widgets.validation_panel import ValidationSummaryPanel

logger = get_logger()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")

        # Set the window icon explicitly
        icon_path = ICONS_DIR / "icon.png"
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.settings_manager = SettingsManager()
        self.board_detector = BoardDetector()
        self.firmware_catalog = FirmwareCatalog()
        self.firmware_configurator = FirmwareConfigurator(self.firmware_catalog)
        self.validation_manager = ValidationManager()

        self.configuration: Optional[RelayConfiguration] = None
        self.project_modified: bool = False
        self.current_project_path: Optional[str] = None

        self._undo_stack: List[str] = []
        self._redo_stack: List[str] = []
        self.upload_thread: Optional[UploadWorkerThread] = None

        self.resize(
            self.settings_manager.settings.window_width,
            self.settings_manager.settings.window_height,
        )

        self._build_menu_bar()
        self._build_ui()
        self._wire_signals()
        self._apply_initial_state()

        logger.info("Main window initialized.")

    def _build_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        new_action = QAction("&New Project", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._on_new_project)
        file_menu.addAction(new_action)

        open_action = QAction("&Open Project...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._on_open_project)
        file_menu.addAction(open_action)

        save_action = QAction("&Save Project", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._on_save_project)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save Project &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self._on_save_project_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edit")

        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut(QKeySequence.Undo)
        self.undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut(QKeySequence.Redo)
        self.redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(self.redo_action)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")

        check_update_action = QAction("&Check for Updates...", self)
        check_update_action.triggered.connect(self._on_check_updates)
        help_menu.addAction(check_update_action)

        manual_action = QAction("&User Manual", self)
        manual_action.triggered.connect(self._on_user_manual)
        help_menu.addAction(manual_action)

        help_menu.addSeparator()

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        top_row = QHBoxLayout()
        self.board_panel = BoardPanel()
        self.firmware_panel = FirmwarePanel()
        top_row.addWidget(self.board_panel, stretch=1)
        top_row.addWidget(self.firmware_panel, stretch=1)
        root_layout.addLayout(top_row)

        self.validation_panel = ValidationSummaryPanel()
        root_layout.addWidget(self.validation_panel)

        splitter = QSplitter(Qt.Vertical)

        # Tabs for Relay Table & Timeline Preview
        self.editor_tabs = QTabWidget()
        self.relay_table = RelayTableWidget()
        self.timeline_widget = TimelineWidget()

        self.editor_tabs.addTab(self.relay_table, "Relay Schedule Table")
        self.editor_tabs.addTab(self.timeline_widget, "Timeline Preview")

        splitter.addWidget(self.editor_tabs)

        console_container = QWidget()
        console_layout = QVBoxLayout(console_container)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_header_row = QHBoxLayout()
        console_header_row.addWidget(QLabel("Console Log"))
        self.clear_console_button = QPushButton("Clear")
        console_header_row.addStretch(1)
        console_header_row.addWidget(self.clear_console_button)
        console_layout.addLayout(console_header_row)

        self.console_panel = ConsolePanel()
        self.console_panel.attach_to_logger(logger)
        console_layout.addWidget(self.console_panel)

        splitter.addWidget(console_container)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root_layout.addWidget(splitter, stretch=1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        root_layout.addWidget(self.progress_bar)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready.")

    def _wire_signals(self) -> None:
        self.board_panel.boardChanged.connect(self._on_board_changed)
        self.board_panel.refreshRequested.connect(self._on_refresh_requested)
        self.board_panel.uploadRequested.connect(self._on_upload_requested)

        self.firmware_panel.channelCountChanged.connect(self._on_channel_count_changed)
        self.firmware_panel.loopTimeChanged.connect(self._on_loop_time_changed)
        self.firmware_panel.activeLowChanged.connect(self._on_config_field_changed)
        self.firmware_panel.brightnessChanged.connect(self._on_config_field_changed)
        self.firmware_panel.countdownChanged.connect(self._on_config_field_changed)

        self.relay_table.configChanged.connect(self._on_relay_updated)
        self.clear_console_button.clicked.connect(self.console_panel.clear_console)

    def _apply_initial_state(self) -> None:
        settings = self.settings_manager.settings
        initial_board = (
            settings.last_board
            if settings.remember_last_board and settings.last_board
            else BOARD_ARDUINO
        )
        index = self.board_panel.board_combo.findText(initial_board)
        if index >= 0:
            self.board_panel.board_combo.setCurrentIndex(index)
        else:
            self._on_board_changed(self.board_panel.current_board())

        # Check for crash recovery
        if not self._check_crash_recovery():
            self.configuration = RelayConfiguration.create_default(initial_board, 2)
            logger.info("Configuration Created")

        if settings.auto_detect_on_launch:
            self._on_refresh_requested()

        self._sync_model_to_gui()
        self._update_undo_redo_actions()

    def _check_crash_recovery(self) -> bool:
        if CRASH_RECOVERY_FILE.exists():
            try:
                reply = QMessageBox.question(
                    self,
                    "Crash Recovery",
                    "An unsaved project session was found from a previous unexpected shutdown.\n"
                    "Would you like to recover this project?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )
                if reply == QMessageBox.Yes:
                    content = CRASH_RECOVERY_FILE.read_text(encoding="utf-8")
                    self.configuration = RelayConfiguration.from_json(content)
                    self.project_modified = True
                    logger.info("Recovered session from crash recovery file.")
                    return True
            except Exception as e:
                logger.error("Failed to read crash recovery file: %s", e)
            finally:
                try:
                    CRASH_RECOVERY_FILE.unlink(missing_ok=True)
                except Exception:
                    pass
        return False

    def _save_undo_snapshot(self) -> None:
        if self.configuration:
            self._undo_stack.append(self.configuration.to_json())
            self._redo_stack.clear()
            self._update_undo_redo_actions()
            self._autosave_recovery()

    def _autosave_recovery(self) -> None:
        if self.configuration:
            try:
                CRASH_RECOVERY_FILE.parent.mkdir(parents=True, exist_ok=True)
                CRASH_RECOVERY_FILE.write_text(self.configuration.to_json(), encoding="utf-8")
            except Exception as e:
                logger.warning("Failed to write crash recovery file: %s", e)

    def _update_undo_redo_actions(self) -> None:
        self.undo_action.setEnabled(len(self._undo_stack) > 0)
        self.redo_action.setEnabled(len(self._redo_stack) > 0)

    def _sync_model_to_gui(self) -> None:
        if not self.configuration:
            return

        self.board_panel.board_combo.blockSignals(True)
        index = self.board_panel.board_combo.findText(self.configuration.board_type)
        if index >= 0:
            self.board_panel.board_combo.setCurrentIndex(index)
        self.board_panel.board_combo.blockSignals(False)

        self.firmware_panel.set_current_channel_count(self.configuration.firmware_type)
        self.firmware_panel.set_loop_time(self.configuration.loop_time)
        self.firmware_panel.set_brightness(self.configuration.display_brightness)
        self.firmware_panel.set_countdown_enabled(self.configuration.countdown_enable)
        self.firmware_panel.set_active_low(self.configuration.relay_active_low)

        self.relay_table.load_channel_configs(self.configuration.relay_list)
        self.timeline_widget.set_configuration(self.configuration)

        self._validate_configuration()
        self._update_status_bar()

    def _mark_project_modified(self) -> None:
        if not self.project_modified:
            self.project_modified = True
            logger.info("Project Modified")
        self._autosave_recovery()
        self._update_status_bar()

    def _validate_configuration(self) -> None:
        if not self.configuration:
            return

        self.firmware_panel.clear_field_errors()
        self.relay_table.clear_field_errors()

        result = self.validation_manager.validate(self.configuration)

        self.validation_panel.set_errors(result.errors)
        self.board_panel.set_upload_enabled(result.is_valid)

        for error in result.errors:
            if error.field == "loop_time":
                self.firmware_panel.set_field_error(error.field, error.message)
            elif error.field.startswith("relay_"):
                parts = error.field.split("_")
                try:
                    row = int(parts[1])
                    if len(parts) == 4:
                        event_idx = int(parts[2])
                        field_type = parts[3]
                        self.relay_table.set_field_error(row, event_idx, field_type, error.message)
                    elif len(parts) == 3:
                        field_type = parts[2]
                        self.relay_table.set_field_error(row, 0, field_type, error.message)
                except ValueError:
                    pass
        self._update_status_bar(result.is_valid)

    def _update_status_bar(self, is_valid: bool = True) -> None:
        path_name = os.path.basename(self.current_project_path) if self.current_project_path else "Untitled"
        mod_flag = "*" if self.project_modified else ""
        valid_status = "Valid" if is_valid else "Invalid"
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - {path_name}{mod_flag}")
        self.statusBar().showMessage(f"Project: {path_name}{mod_flag} | Configuration: {valid_status}")

    # Menu Slots
    def _on_new_project(self) -> None:
        if self.project_modified:
            res = QMessageBox.question(
                self, "New Project", "Save changes to current project?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if res == QMessageBox.Cancel:
                return
            if res == QMessageBox.Yes:
                self._on_save_project()

        board = self.board_panel.current_board()
        self.configuration = RelayConfiguration.create_default(board, 2)
        self.current_project_path = None
        self.project_modified = False
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._update_undo_redo_actions()
        self._sync_model_to_gui()
        logger.info("New project created.")

    def _on_open_project(self) -> None:
        if self.project_modified:
            res = QMessageBox.question(
                self, "Open Project", "Save changes to current project?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if res == QMessageBox.Cancel:
                return
            if res == QMessageBox.Yes:
                self._on_save_project()

        path, _ = QFileDialog.getOpenFileName(
            self, "Open Relay Project", "", "JSON Project Files (*.json);;All Files (*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.configuration = RelayConfiguration.from_json(f.read())
                self.current_project_path = path
                self.project_modified = False
                self._undo_stack.clear()
                self._redo_stack.clear()
                self._update_undo_redo_actions()
                self._sync_model_to_gui()
                logger.info("Opened project: %s", path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open project file:\n{e}")

    def _on_save_project(self) -> bool:
        if not self.current_project_path:
            return self._on_save_project_as()

        try:
            with open(self.current_project_path, "w", encoding="utf-8") as f:
                f.write(self.configuration.to_json())
            self.project_modified = False
            CRASH_RECOVERY_FILE.unlink(missing_ok=True)
            self._update_status_bar()
            logger.info("Saved project: %s", self.current_project_path)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project file:\n{e}")
            return False

    def _on_save_project_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", "relay_config.json", "JSON Project Files (*.json);;All Files (*)"
        )
        if path:
            self.current_project_path = path
            return self._on_save_project()
        return False

    def _on_undo(self) -> None:
        if not self._undo_stack:
            return
        self._redo_stack.append(self.configuration.to_json())
        prev_json = self._undo_stack.pop()
        self.configuration = RelayConfiguration.from_json(prev_json)
        self._sync_model_to_gui()
        self._update_undo_redo_actions()
        logger.info("Undo executed.")

    def _on_redo(self) -> None:
        if not self._redo_stack:
            return
        self._undo_stack.append(self.configuration.to_json())
        next_json = self._redo_stack.pop()
        self.configuration = RelayConfiguration.from_json(next_json)
        self._sync_model_to_gui()
        self._update_undo_redo_actions()
        logger.info("Redo executed.")

    def _on_check_updates(self) -> None:
        self.statusBar().showMessage("Checking for updates...")
        update = check_for_updates()
        if update:
            QMessageBox.information(
                self,
                "Update Available",
                f"A new version ({update['version']}) of {APP_NAME} is available!\n\n"
                f"Release Notes:\n{update['notes']}\n\n"
                f"Download from: {update['url']}",
            )
        else:
            QMessageBox.information(
                self,
                "No Updates",
                f"{APP_NAME} v{APP_VERSION} is currently up to date.",
            )
        self._update_status_bar()

    def _on_user_manual(self) -> None:
        manual_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "UserManual.md")
        msg = f"User Manual is located at:\n{os.path.abspath(manual_path)}\n\nPlease refer to this document for operating instructions."
        QMessageBox.information(self, "User Manual", msg)

    def _on_about(self) -> None:
        about = QMessageBox(self)
        about.setWindowTitle(f"About {APP_NAME}")
        about.setText(
            f"<b>{APP_NAME} v{APP_VERSION}</b><br><br>"
            "An industrial relay timing configuration &amp; hardware flashing tool.<br>"
            "Supports Arduino UNO, Nano, and ESP32 platforms with live validation and timing preview."
        )
        icon_path = ICONS_DIR / "icon_64.png"
        if icon_path.is_file():
            from PySide6.QtGui import QPixmap
            about.setIconPixmap(QPixmap(str(icon_path)))
        about.exec()

    # Component slots
    def _on_board_changed(self, board: str) -> None:
        if not self.configuration: return
        self._save_undo_snapshot()
        logger.info("Board Changed: %s", board)
        counts = self.firmware_catalog.available_channel_counts(board)
        self.firmware_panel.set_available_channel_counts(counts)
        self.settings_manager.update(last_board=board)
        self.board_panel.set_status("Not Detected", is_connected=False)

        self.configuration.board_type = board
        self._mark_project_modified()
        self._sync_model_to_gui()

    def _on_channel_count_changed(self, channel_count: int) -> None:
        if not self.configuration: return
        self._save_undo_snapshot()
        logger.info("Firmware Changed: %s Relay", channel_count)

        old_relays = self.configuration.relay_list
        new_relays = []
        for i in range(channel_count):
            if i < len(old_relays):
                new_relays.append(old_relays[i])
            else:
                new_relays.append(RelayObject(relay_number=i))

        self.configuration.firmware_type = channel_count
        self.configuration.relay_list = new_relays
        self._mark_project_modified()
        self._sync_model_to_gui()

    def _on_loop_time_changed(self, value: int) -> None:
        if not self.configuration: return
        self._save_undo_snapshot()
        self.configuration.loop_time = value
        self._mark_project_modified()
        self.timeline_widget.set_configuration(self.configuration)
        self._validate_configuration()

    def _on_config_field_changed(self, *_args) -> None:
        if not self.configuration: return
        self._save_undo_snapshot()
        self.configuration.display_brightness = self.firmware_panel.current_brightness()
        self.configuration.countdown_enable = self.firmware_panel.is_countdown_enabled()
        self.configuration.relay_active_low = self.firmware_panel.is_active_low()
        self._mark_project_modified()
        self.timeline_widget.set_configuration(self.configuration)
        self._validate_configuration()

    def _on_relay_updated(self) -> None:
        if not self.configuration: return
        self._save_undo_snapshot()
        self.configuration.relay_list = self.relay_table.get_channel_configs()
        self._mark_project_modified()
        self.timeline_widget.set_configuration(self.configuration)
        self._validate_configuration()

    def _on_refresh_requested(self) -> None:
        board = self.board_panel.current_board()
        logger.info("Refresh requested for board: %s", board)
        self.board_panel.set_status(STATUS_DETECTING, is_connected=False)
        self.statusBar().showMessage(f"Detecting {board}...")

        info = self.board_detector.detect(board)
        status_text = self.board_detector.status_label(info)
        self.board_panel.set_status(status_text, is_connected=info.is_connected)
        self.board_panel.set_upload_enabled(info.is_connected)
        self._update_status_bar()

    def _on_upload_requested(self) -> None:
        if not self.configuration: return
        profile = self.configuration
        board = profile.board_type

        logger.info("Upload requested: board=%s channels=%s", board, profile.firmware_type)
        self.firmware_configurator.apply_profile(profile)

        uploader_cls = ArduinoUploader if board == BOARD_ARDUINO else ESP32Uploader
        uploader = uploader_cls(
            com_port=self.board_detector.last_result.com_port,
            profile=profile,
        )

        self.board_panel.set_upload_enabled(False)
        self.progress_bar.setValue(0)

        self.upload_thread = UploadWorkerThread(uploader)
        self.upload_thread.progress.connect(self._on_upload_progress)
        self.upload_thread.finished.connect(self._on_upload_finished)
        self.upload_thread.start()

    def _on_upload_progress(self, percent: int, message: str) -> None:
        self.progress_bar.setValue(percent)
        self.statusBar().showMessage(message)

    def _on_upload_finished(self, success: bool, message: str) -> None:
        self.board_panel.set_upload_enabled(True)
        if success:
            self.progress_bar.setValue(100)
            self.statusBar().showMessage("Upload Successful!")
            QMessageBox.information(self, "Upload Complete", "Firmware was successfully configured and uploaded.")
        else:
            self.statusBar().showMessage("Upload Failed!")
            QMessageBox.critical(self, "Upload Error", f"Upload failed:\n{message}")

    def closeEvent(self, event) -> None:
        if self.project_modified:
            res = QMessageBox.question(
                self, "Exit", "Save changes before closing?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if res == QMessageBox.Cancel:
                event.ignore()
                return
            if res == QMessageBox.Yes:
                if not self._on_save_project():
                    event.ignore()
                    return

        CRASH_RECOVERY_FILE.unlink(missing_ok=True)
        self.settings_manager.update(
            window_width=self.width(),
            window_height=self.height(),
        )
        logger.info("Application closing, settings saved.")
        super().closeEvent(event)
