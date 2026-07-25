"""
main_window.py
================================================================================
MainWindow: assembles every widget in ui/widgets/ into the application's
single top-level window, and wires their Qt signals to the core.* logic
classes (BoardDetector, FirmwareCatalog, uploader placeholders).

This module is intentionally "thin" -- it contains layout and signal/slot
wiring only. Every piece of actual behavior (detection, cataloging,
uploading) lives in core/, so this file stays readable as the project
grows and stays easy to unit-test the logic layer independently of Qt.
================================================================================
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.board_detector import BoardDetector
from core.constants import APP_NAME, APP_VERSION, STATUS_DETECTING
from core.firmware_manager import FirmwareCatalog, FirmwareConfigurator
from core.logger import get_logger
from core.models import RelayConfiguration, RelayObject
from core.settings_manager import SettingsManager
from core.uploader import ArduinoUploader, ESP32Uploader
from core.constants import BOARD_ARDUINO
from core.validation_manager import ValidationManager

from ui.widgets.board_panel import BoardPanel
from ui.widgets.console_panel import ConsolePanel
from ui.widgets.firmware_panel import FirmwarePanel
from ui.widgets.relay_table import RelayTableWidget
from ui.widgets.validation_panel import ValidationSummaryPanel

logger = get_logger()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")

        # ---- Core / logic-layer objects (no Qt dependency inside these) --
        self.settings_manager = SettingsManager()
        self.board_detector = BoardDetector()
        self.firmware_catalog = FirmwareCatalog()
        self.firmware_configurator = FirmwareConfigurator(self.firmware_catalog)
        self.validation_manager = ValidationManager()

        self.configuration: RelayConfiguration = None
        self.project_modified: bool = False

        self.resize(
            self.settings_manager.settings.window_width,
            self.settings_manager.settings.window_height,
        )

        self._build_ui()
        self._wire_signals()
        self._apply_initial_state()

        logger.info("Main window initialized.")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        # ---- Top row: board + firmware configuration panels ------------
        top_row = QHBoxLayout()
        self.board_panel = BoardPanel()
        self.firmware_panel = FirmwarePanel()
        top_row.addWidget(self.board_panel, stretch=1)
        top_row.addWidget(self.firmware_panel, stretch=1)
        root_layout.addLayout(top_row)
        
        # ---- Validation Summary Panel -----------------------------------
        self.validation_panel = ValidationSummaryPanel()
        root_layout.addWidget(self.validation_panel)

        # ---- Middle: relay table (top) / console (bottom), resizable ---
        splitter = QSplitter(Qt.Vertical)

        self.relay_table = RelayTableWidget()
        splitter.addWidget(self.relay_table)

        console_container = QWidget()
        console_layout = QVBoxLayout(console_container)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_header_row = QHBoxLayout()
        console_header_row.addWidget(QLabel("Console"))
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

        # ---- Progress bar -------------------------------------------------
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        root_layout.addWidget(self.progress_bar)

        # ---- Status bar -----------------------------------------------------
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
        # Restore last-used board if the setting allows, else default to
        # the first supported board.
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

        if settings.auto_detect_on_launch:
            self._on_refresh_requested()
            
        self.configuration = RelayConfiguration.create_default(initial_board, 2)
        logger.info("Configuration Created")
        self._sync_model_to_gui()

    # ------------------------------------------------------------------
    # Data Sync
    # ------------------------------------------------------------------
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

        self._validate_configuration()
        self._update_status_bar()

    def _mark_project_modified(self) -> None:
        if not self.project_modified:
            self.project_modified = True
            logger.info("Project Modified")
            self._update_status_bar()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
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
                # format: relay_0_start
                parts = error.field.split("_")
                if len(parts) == 3:
                    try:
                        row = int(parts[1])
                        field_type = parts[2]
                        self.relay_table.set_field_error(row, field_type, error.message)
                    except ValueError:
                        pass
        self._update_status_bar(result.is_valid)

    def _update_status_bar(self, is_valid: bool = True) -> None:
        status = "Project Modified" if self.project_modified else "Configuration Ready"
        valid_status = "Configuration Valid" if is_valid else "Configuration Invalid"
        self.statusBar().showMessage(f"{status} | {valid_status}")

    def _on_board_changed(self, board: str) -> None:
        if not self.configuration: return
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
        logger.info("Firmware Changed: %s Relay", channel_count)
        
        # Adjust relays in model
        old_relays = self.configuration.relay_list
        new_relays = []
        for i in range(channel_count):
            if i < len(old_relays):
                new_relays.append(old_relays[i])
            else:
                new_relays.append(RelayObject(relay_number=i))
                logger.info("Relay Added")
                
        if len(old_relays) > channel_count:
            for _ in range(len(old_relays) - channel_count):
                logger.info("Relay Removed")
                
        self.configuration.firmware_type = channel_count
        self.configuration.relay_list = new_relays
        logger.info("Configuration Updated")
        
        self._mark_project_modified()
        self._sync_model_to_gui()

    def _on_loop_time_changed(self, value: int) -> None:
        if not self.configuration: return
        self.configuration.loop_time = value
        logger.info("Configuration Updated")
        self._mark_project_modified()
        self._validate_configuration()
        
    def _on_config_field_changed(self, *_args) -> None:
        if not self.configuration: return
        self.configuration.display_brightness = self.firmware_panel.current_brightness()
        self.configuration.countdown_enable = self.firmware_panel.is_countdown_enabled()
        self.configuration.relay_active_low = self.firmware_panel.is_active_low()
        logger.info("Configuration Updated")
        self._mark_project_modified()
        self._validate_configuration()
        
    def _on_relay_updated(self) -> None:
        if not self.configuration: return
        self.configuration.relay_list = self.relay_table.get_channel_configs()
        logger.info("Configuration Updated")
        self._mark_project_modified()
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

        logger.info(
            "Upload requested: board=%s channels=%s loop_time=%ss active_low=%s brightness=%s countdown=%s",
            profile.board_type,
            profile.firmware_type,
            profile.loop_time,
            profile.relay_active_low,
            profile.display_brightness,
            profile.countdown_enable,
        )

        # Firmware configuration writing is a placeholder in this phase.
        self.firmware_configurator.apply_profile(profile)

        uploader_cls = ArduinoUploader if board == BOARD_ARDUINO else ESP32Uploader
        uploader = uploader_cls(
            com_port=self.board_detector.last_result.com_port,
            profile=profile,
            progress_callback=self._on_upload_progress,
        )
        uploader.run()

    def _on_upload_progress(self, percent: int, message: str) -> None:
        self.progress_bar.setValue(percent)
        self.statusBar().showMessage(message)

    # ------------------------------------------------------------------
    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self.settings_manager.update(
            window_width=self.width(),
            window_height=self.height(),
        )
        logger.info("Application closing, settings saved.")
        super().closeEvent(event)
