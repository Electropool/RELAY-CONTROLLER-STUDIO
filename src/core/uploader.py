from __future__ import annotations

import sys
import os
import io
import urllib.request
import zipfile
import subprocess
import shutil
from pathlib import Path
from enum import Enum, auto
from typing import Callable, Optional, List
from PySide6.QtCore import QObject, Signal, QThread



class UploadWorkerThread(QThread):
    progress = Signal(int, str)
    finished = Signal(bool, str)

    def __init__(self, uploader: BaseUploader, parent=None):
        super().__init__(parent)
        self.uploader = uploader
        # Route progress signals through worker thread
        self.uploader.signals.progress.connect(self._on_progress)

    def _on_progress(self, percent: int, msg: str):
        self.progress.emit(percent, msg)

    def run(self):
        try:
            success = self.uploader.run()
            msg = "Upload successful!" if success else "Upload failed."
            self.finished.emit(success, msg)
        except Exception as e:
            logger.error("Error during upload thread: %s", e)
            self.finished.emit(False, str(e))


from core.constants import (
    TOOLS_DIR,
    PROJECT_ROOT,
    BOARD_ARDUINO,
    BOARD_ESP32,
    UPLOAD_COMPILING,
    UPLOAD_FAILED,
    UPLOAD_IDLE,
    UPLOAD_PREPARING,
    UPLOAD_SUCCESS,
    UPLOAD_UPLOADING,
)
from core.logger import get_logger
from core.models import RelayConfiguration

logger = get_logger()


class UploadStage(Enum):
    IDLE = auto()
    PREPARING = auto()
    COMPILING = auto()
    UPLOADING = auto()
    SUCCESS = auto()
    FAILED = auto()


STAGE_LABELS = {
    UploadStage.IDLE: UPLOAD_IDLE,
    UploadStage.PREPARING: UPLOAD_PREPARING,
    UploadStage.COMPILING: UPLOAD_COMPILING,
    UploadStage.UPLOADING: UPLOAD_UPLOADING,
    UploadStage.SUCCESS: UPLOAD_SUCCESS,
    UploadStage.FAILED: UPLOAD_FAILED,
}


class UploadSignals(QObject):
    """Signals for communicating with the GUI thread during background upload."""
    progress = Signal(int, str)  # percent, message


def write_arduino_cli_yaml(yaml_path: Path):
    """Write a local arduino-cli configuration to keep the toolchain 100% portable."""
    data_dir = (TOOLS_DIR / "Arduino15").resolve()
    downloads_dir = (data_dir / "staging").resolve()
    user_dir = (TOOLS_DIR / "Arduino").resolve()

    data_dir.mkdir(parents=True, exist_ok=True)
    downloads_dir.mkdir(parents=True, exist_ok=True)
    user_dir.mkdir(parents=True, exist_ok=True)

    yaml_content = f"""directories:
  data: {data_dir.as_posix()}
  downloads: {downloads_dir.as_posix()}
  user: {user_dir.as_posix()}
board_manager:
  additional_urls:
    - https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
"""
    yaml_path.write_text(yaml_content, encoding="utf-8")


def ensure_arduino_cli() -> Path:
    """Ensure arduino-cli is present, using local, bundled, or downloaded versions."""
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    exe_name = "arduino-cli.exe" if sys.platform == "win32" else "arduino-cli"
    cli_path = TOOLS_DIR / exe_name

    if cli_path.is_file():
        return cli_path

    # Check for PyInstaller bundled version
    if getattr(sys, "frozen", False):
        meipass = Path(sys._MEIPASS)
        bundled = meipass / "tools" / exe_name
        if bundled.is_file():
            logger.info("Copying bundled arduino-cli to %s", cli_path)
            shutil.copy2(bundled, cli_path)
            return cli_path

    # Download from official URL
    url = "https://github.com/arduino/arduino-cli/releases/download/v1.0.4/arduino-cli_1.0.4_Windows_64bit.zip"
    logger.info("Arduino CLI not found. Downloading from %s...", url)
    try:
        response = urllib.request.urlopen(url, timeout=30)
        zip_data = response.read()
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            zf.extract(exe_name, path=str(TOOLS_DIR))
        logger.info("Downloaded and extracted arduino-cli successfully.")
        return cli_path
    except Exception as e:
        raise RuntimeError(
            f"Failed to download/install Arduino CLI: {e}. "
            "Please check internet connection or manually place arduino-cli in tools/ directory."
        )


class BaseUploader:
    def __init__(
        self,
        com_port: str,
        profile: RelayConfiguration,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ):
        self.com_port = com_port
        self.profile = profile
        self.progress_callback = progress_callback
        self.stage = UploadStage.IDLE
        self.signals = UploadSignals()
        if progress_callback:
            self.signals.progress.connect(progress_callback)

    def _set_stage(self, stage: UploadStage, message: str) -> None:
        self.stage = stage
        logger.info("[%s] %s: %s", type(self).__name__, STAGE_LABELS[stage], message)
        percent_by_stage = {
            UploadStage.PREPARING: 10,
            UploadStage.COMPILING: 50,
            UploadStage.UPLOADING: 80,
            UploadStage.SUCCESS: 100,
            UploadStage.FAILED: 0,
        }
        self.signals.progress.emit(percent_by_stage.get(stage, 0), message)

    def get_cli_args(self, subcommand: str) -> List[str]:
        cli_exe = ensure_arduino_cli()
        yaml_path = TOOLS_DIR / "arduino-cli.yaml"
        write_arduino_cli_yaml(yaml_path)
        return [str(cli_exe), "--config-file", str(yaml_path), subcommand]

    def run_process(self, args: List[str], stage_desc: str) -> bool:
        """Run an arduino-cli subcommand, logging output line by line."""
        logger.info("Executing: %s", " ".join(args))
        try:
            # Prevent showing command window on Windows release builds
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                startupinfo=startupinfo,
            )

            # Stream output to log (which shows up in GUI ConsolePanel)
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                stripped = line.strip()
                if stripped:
                    logger.info("[%s] %s", stage_desc, stripped)

            proc.wait()
            return proc.returncode == 0
        except Exception as e:
            logger.error("Process execution failed: %s", e)
            return False

    def ensure_board_package(self, core_name: str) -> bool:
        """Checks core list, installs target package if missing."""
        args_list = self.get_cli_args("core") + ["list"]
        logger.info("Checking board packages...")
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            output = subprocess.check_output(args_list, text=True, startupinfo=startupinfo)
            if core_name in output:
                return True
        except Exception:
            pass

        self._set_stage(UploadStage.PREPARING, f"Installing board package {core_name}...")
        
        # Run core update-index first
        update_args = self.get_cli_args("core") + ["update-index"]
        self.run_process(update_args, "Preparing")

        # Install target core
        install_args = self.get_cli_args("core") + ["install", core_name]
        return self.run_process(install_args, "Preparing")

    def ensure_libraries(self) -> bool:
        """Ensure TM1637 library is installed."""
        args_list = self.get_cli_args("lib") + ["list"]
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            output = subprocess.check_output(args_list, text=True, startupinfo=startupinfo)
            if "TM1637" in output:
                return True
        except Exception:
            pass

        self._set_stage(UploadStage.PREPARING, "Installing TM1637 library...")
        install_args = self.get_cli_args("lib") + ["install", "TM1637"]
        return self.run_process(install_args, "Preparing")

    def prepare(self) -> bool:
        self._set_stage(UploadStage.PREPARING, "Initializing toolchain...")
        try:
            ensure_arduino_cli()
            if not self.ensure_libraries():
                logger.error("Failed to setup required libraries.")
                return False
            return True
        except Exception as e:
            logger.error("Preparation failed: %s", e)
            return False

    def compile_sketch(self, fqbn: str, sketch_path: Path) -> bool:
        self._set_stage(UploadStage.COMPILING, f"Compiling sketch for {fqbn}...")
        sketch_dir = sketch_path.parent
        compile_args = self.get_cli_args("compile") + ["--fqbn", fqbn, str(sketch_dir)]
        
        logger.info("--- Compile Step ---")
        logger.info("Sketch Folder: %s", sketch_dir)
        logger.info("Sketch File: %s", sketch_path)
        logger.info("Compile Command: %s", " ".join(compile_args))
        
        return self.run_process(compile_args, "Compiling")

    def upload_sketch(self, fqbn: str, sketch_path: Path) -> bool:
        self._set_stage(UploadStage.UPLOADING, f"Uploading to {self.com_port}...")
        if not self.com_port:
            logger.error("Upload failed: No COM port detected/provided.")
            return False
        
        # Test connection/permission prior to flashing
        try:
            import serial
            s = serial.Serial(self.com_port)
            s.close()
        except serial.SerialException as se:
            if "PermissionError" in str(se) or "Access is denied" in str(se):
                logger.error("Upload Error: Port %s is busy. Close serial monitor.", self.com_port)
            else:
                logger.error("Upload Error: Cannot open port %s (%s)", self.com_port, se)
            return False

        sketch_dir = sketch_path.parent
        upload_args = self.get_cli_args("upload") + ["-p", self.com_port, "--fqbn", fqbn, str(sketch_dir)]
        
        logger.info("--- Upload Step ---")
        logger.info("Sketch Folder: %s", sketch_dir)
        logger.info("Sketch File: %s", sketch_path)
        logger.info("Upload Command: %s", " ".join(upload_args))
        
        return self.run_process(upload_args, "Uploading")

    def run(self) -> bool:
        raise NotImplementedError("Subclasses must implement run()")


class ArduinoUploader(BaseUploader):
    def run(self) -> bool:
        logger.info("Starting Arduino Upload process...")
        if not self.prepare():
            self._set_stage(UploadStage.FAILED, "Setup failed")
            return False

        if not self.ensure_board_package("arduino:avr"):
            self._set_stage(UploadStage.FAILED, "Board package installation failed")
            return False

        from core.firmware_manager import FirmwareCatalog
        catalog = FirmwareCatalog()
        if not catalog.sketch_exists(self.profile.board_type, self.profile.firmware_type):
            err_msg = f"Firmware template not found for {self.profile.board_type} {self.profile.firmware_type}CH"
            self._set_stage(UploadStage.FAILED, err_msg)
            logger.error("Sketch file not found at expected path: %s", catalog.sketch_path(self.profile.board_type, self.profile.firmware_type))
            return False

        sketch_path = catalog.sketch_path(self.profile.board_type, self.profile.firmware_type)

        # Build configurations inside sketch
        from core.firmware_manager import FirmwareConfigurator
        configurator = FirmwareConfigurator(catalog)
        if not configurator.apply_profile(self.profile):
            self._set_stage(UploadStage.FAILED, "Failed to write configuration variables")
            return False

        # Attempt to compile
        fqbn = "arduino:avr:uno"
        if not self.compile_sketch(fqbn, sketch_path):
            self._set_stage(UploadStage.FAILED, "Compilation failed")
            return False

        # Attempt standard upload
        fqbn_upload = "arduino:avr:uno"
        # We can try to upload as Uno. If that fails, try Nano with new bootloader, then old bootloader.
        # This covers all potential UNO/Nano options automatically!
        logger.info("Attempting upload to Uno...")
        if self.upload_sketch(fqbn_upload, sketch_path):
            self._set_stage(UploadStage.SUCCESS, "Upload Success (Uno)")
            return True

        logger.warning("Uno upload failed. Trying Nano (New Bootloader)...")
        fqbn_nano = "arduino:avr:nano"
        if self.upload_sketch(fqbn_nano, sketch_path):
            self._set_stage(UploadStage.SUCCESS, "Upload Success (Nano)")
            return True

        logger.warning("Nano upload failed. Trying Nano (Old Bootloader)...")
        fqbn_nano_old = "arduino:avr:nano:cpu=atmega328old"
        if self.upload_sketch(fqbn_nano_old, sketch_path):
            self._set_stage(UploadStage.SUCCESS, "Upload Success (Nano - Old Bootloader)")
            return True

        self._set_stage(UploadStage.FAILED, "Upload failed on all configurations (Uno/Nano)")
        return False


class ESP32Uploader(BaseUploader):
    def run(self) -> bool:
        logger.info("Starting ESP32 Upload process...")
        if not self.prepare():
            self._set_stage(UploadStage.FAILED, "Setup failed")
            return False

        if not self.ensure_board_package("esp32:esp32"):
            self._set_stage(UploadStage.FAILED, "Board package installation failed")
            return False

        from core.firmware_manager import FirmwareCatalog
        catalog = FirmwareCatalog()
        if not catalog.sketch_exists(self.profile.board_type, self.profile.firmware_type):
            err_msg = f"Firmware template not found for {self.profile.board_type} {self.profile.firmware_type}CH"
            self._set_stage(UploadStage.FAILED, err_msg)
            logger.error("Sketch file not found at expected path: %s", catalog.sketch_path(self.profile.board_type, self.profile.firmware_type))
            return False

        sketch_path = catalog.sketch_path(self.profile.board_type, self.profile.firmware_type)

        # Build configurations inside sketch
        from core.firmware_manager import FirmwareConfigurator
        configurator = FirmwareConfigurator(catalog)
        if not configurator.apply_profile(self.profile):
            self._set_stage(UploadStage.FAILED, "Failed to write configuration variables")
            return False

        fqbn = "esp32:esp32:esp32"
        # Compile
        if not self.compile_sketch(fqbn, sketch_path):
            self._set_stage(UploadStage.FAILED, "Compilation failed")
            return False

        # Upload
        if not self.upload_sketch(fqbn, sketch_path):
            self._set_stage(UploadStage.FAILED, "Upload failed")
            return False

        self._set_stage(UploadStage.SUCCESS, "Upload Success")
        return True
