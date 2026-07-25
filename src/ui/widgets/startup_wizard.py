import sys
import threading
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QMessageBox
)
from core.logger import get_logger
from core.constants import TOOLS_DIR, DRIVERS_DIR
from core.uploader import ensure_arduino_cli, write_arduino_cli_yaml

logger = get_logger()


class WizardSignals(QObject):
    log = Signal(str)
    progress = Signal(int)
    item_status = Signal(str, str)  # item_id, status_text ('pending', 'running', 'success', 'failed')
    finished = Signal(bool, str)    # success, error_message


class StartupWizardDialog(QDialog):
    Accepted = 1
    Rejected = 0

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Relay Controller Studio - Setup Wizard")
        self.resize(600, 450)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.signals = WizardSignals()
        self.signals.log.connect(self._on_log)
        self.signals.progress.connect(self.progress_bar.setValue)
        self.signals.item_status.connect(self._on_item_status)
        self.signals.finished.connect(self._on_finished)

        self._build_ui()
        self.is_running = False

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        title_label = QLabel("Portable Toolchain Setup Wizard")
        title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #61afef;")
        layout.addWidget(title_label)

        desc = QLabel(
            "This setup wizard will download and configure a fully portable, self-contained "
            "development toolchain (Arduino CLI, board packages, and libraries) in a local "
            "folder next to this application. No system-wide settings or administrator "
            "privileges are modified."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #abb2bf; line-height: 18px;")
        layout.addWidget(desc)

        # Checklist Group
        self.items = {
            "cli": QLabel("⏳ Arduino CLI Executive... Pending"),
            "avr": QLabel("⏳ Arduino AVR Board Core... Pending"),
            "esp": QLabel("⏳ ESP32 Board Core... Pending"),
            "lib": QLabel("⏳ TM1637 Countdown Library... Pending"),
        }
        for item in self.items.values():
            item.setStyleSheet("font-size: 13px; font-weight: 600; color: #abb2bf;")
            layout.addWidget(item)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        layout.addWidget(self.progress_bar)

        # Output Log Box
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Setup logs will print here...")
        self.log_box.setStyleSheet(
            "background-color: #16171a; border: 1px solid #3a3d41; "
            "font-family: Consolas, monospace; font-size: 11px; color: #abb2bf;"
        )
        layout.addWidget(self.log_box)

        # Buttons
        btn_row = QHBoxLayout()
        self.install_btn = QPushButton("Start Setup")
        self.install_btn.setStyleSheet("font-weight: 600;")
        self.install_btn.clicked.connect(self.start_install)

        self.driver_btn = QPushButton("USB Drivers Guide")
        self.driver_btn.clicked.connect(self.show_driver_guide)

        self.launch_btn = QPushButton("Launch Application")
        self.launch_btn.setEnabled(False)
        self.launch_btn.setStyleSheet("font-weight: 600; background-color: #2f5233; border-color: #4a7c4f;")
        self.launch_btn.clicked.connect(self.accept)

        btn_row.addWidget(self.driver_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.install_btn)
        btn_row.addWidget(self.launch_btn)
        layout.addLayout(btn_row)

    def _on_log(self, text: str) -> None:
        self.log_box.append(text)
        self.log_box.moveCursor(self.log_box.textCursor().End)

    def _on_item_status(self, item_id: str, status: str) -> None:
        lbl = self.items.get(item_id)
        if not lbl:
            return
        prefix = {
            "cli": "Arduino CLI Executive",
            "avr": "Arduino AVR Board Core",
            "esp": "ESP32 Board Core",
            "lib": "TM1637 Countdown Library",
        }[item_id]

        if status == "running":
            lbl.setText(f"⚙️ {prefix}... Running")
            lbl.setStyleSheet("color: #61afef; font-weight: 600;")
        elif status == "success":
            lbl.setText(f"✅ {prefix}... Complete")
            lbl.setStyleSheet("color: #98c379; font-weight: 600;")
        elif status == "failed":
            lbl.setText(f"❌ {prefix}... Failed")
            lbl.setStyleSheet("color: #e06c75; font-weight: 600;")
        else:
            lbl.setText(f"⏳ {prefix}... Pending")
            lbl.setStyleSheet("color: #abb2bf; font-weight: 600;")

    def show_driver_guide(self) -> None:
        QMessageBox.information(
            self,
            "USB Serial Drivers Guide",
            "If your computer does not recognize connected board(s) (e.g. no COM port shows up), "
            "you may need USB drivers:\n\n"
            "1. CH340 / CH341 Drivers: Commonly used on cheap clones.\n"
            "2. CP210x Drivers: Common on ESP32 Dev modules.\n"
            "3. FTDI Drivers: Common on older genuine Nano/Uno.\n\n"
            "These driver installer executables can be found under the 'drivers/' folder "
            "in your installation directory. Double-click to install them as admin."
        )

    def start_install(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self.install_btn.setEnabled(False)
        self.signals.log.emit("Starting local portable toolchain installation...")
        threading.Thread(target=self._run_install_thread, daemon=True).start()

    def _run_install_thread(self) -> None:
        try:
            self.signals.progress.emit(5)
            
            # 1. Setup CLI
            self.signals.item_status.emit("cli", "running")
            self.signals.log.emit("Initializing Arduino CLI...")
            cli_path = ensure_arduino_cli()
            yaml_path = TOOLS_DIR / "arduino-cli.yaml"
            write_arduino_cli_yaml(yaml_path)
            self.signals.item_status.emit("cli", "success")
            self.signals.progress.emit(25)

            # Prevent command window popup on Windows
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            # Run core update-index
            self.signals.log.emit("Downloading board packages index...")
            args = [str(cli_path), "--config-file", str(yaml_path), "core", "update-index"]
            subprocess.check_call(args, startupinfo=startupinfo)
            self.signals.progress.emit(35)

            # 2. Install Arduino AVR Core
            self.signals.item_status.emit("avr", "running")
            self.signals.log.emit("Installing arduino:avr core...")
            args = [str(cli_path), "--config-file", str(yaml_path), "core", "install", "arduino:avr"]
            subprocess.check_call(args, startupinfo=startupinfo)
            self.signals.item_status.emit("avr", "success")
            self.signals.progress.emit(55)

            # 3. Install ESP32 Core
            self.signals.item_status.emit("esp", "running")
            self.signals.log.emit("Installing esp32:esp32 core...")
            args = [str(cli_path), "--config-file", str(yaml_path), "core", "install", "esp32:esp32"]
            subprocess.check_call(args, startupinfo=startupinfo)
            self.signals.item_status.emit("esp", "success")
            self.signals.progress.emit(85)

            # 4. Install TM1637 Lib
            self.signals.item_status.emit("lib", "running")
            self.signals.log.emit("Installing TM1637 Countdown Library...")
            args = [str(cli_path), "--config-file", str(yaml_path), "lib", "install", "TM1637"]
            subprocess.check_call(args, startupinfo=startupinfo)
            self.signals.item_status.emit("lib", "success")
            self.signals.progress.emit(100)

            self.signals.finished.emit(True, "")
        except Exception as e:
            logger.exception("First startup wizard failed: %s", e)
            self.signals.finished.emit(False, str(e))

    def _on_finished(self, success: bool, err_msg: str) -> None:
        self.is_running = False
        self.install_btn.setEnabled(True)
        if success:
            self.signals.log.emit("\n🎉 Toolchain installation complete! Click 'Launch Application' to begin.")
            self.launch_btn.setEnabled(True)
            self.settings_manager.update(first_startup_complete=True)
        else:
            self.signals.log.emit(f"\n❌ Error during setup: {err_msg}")
            QMessageBox.critical(
                self,
                "Setup Failed",
                f"An error occurred during setup:\n{err_msg}\n\nPlease check your internet connection and try again."
            )
            # Find which items were running and mark them failed
            for item_id, label in self.items.items():
                if "Running" in label.text():
                    self.signals.item_status.emit(item_id, "failed")
