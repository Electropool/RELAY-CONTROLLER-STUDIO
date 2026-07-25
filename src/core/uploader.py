"""
uploader.py
================================================================================
PHASE 1 PLACEHOLDER MODULE.

Defines the class architecture for flashing firmware onto a connected
board, without implementing any actual compilation or upload logic.

Explicitly OUT OF SCOPE for this phase (per project requirements):
  - No Arduino CLI invocation.
  - No esptool invocation.
  - No actual compilation or flashing of any kind.

Design notes for the future implementation:
  - BaseUploader defines the common lifecycle (prepare -> compile ->
    upload -> done) as separate steps so the GUI's progress bar and
    console panel can be driven from well-defined stage transitions
    instead of one opaque "do everything" call.
  - ArduinoUploader will eventually wrap the `arduino-cli` binary
    (compile + upload sub-commands) via QProcess so output streams live
    into the console panel.
  - ESP32Uploader will eventually wrap `arduino-cli` (for compilation,
    since the sketches are standard .ino files) and/or `esptool.py`
    directly for the flashing step.
  - Both classes are designed to run on a background QThread so upload
    progress never blocks the GUI event loop.
================================================================================
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Optional

from core.constants import (
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
    """Discrete stages of the (future) flashing pipeline."""

    IDLE = auto()
    PREPARING = auto()
    COMPILING = auto()
    UPLOADING = auto()
    SUCCESS = auto()
    FAILED = auto()


# Human-readable label for each stage, matching the strings already
# defined in core.constants so the GUI has one consistent vocabulary.
STAGE_LABELS = {
    UploadStage.IDLE: UPLOAD_IDLE,
    UploadStage.PREPARING: UPLOAD_PREPARING,
    UploadStage.COMPILING: UPLOAD_COMPILING,
    UploadStage.UPLOADING: UPLOAD_UPLOADING,
    UploadStage.SUCCESS: UPLOAD_SUCCESS,
    UploadStage.FAILED: UPLOAD_FAILED,
}


class BaseUploader:
    """
    Common placeholder interface shared by every board-specific uploader.

    Parameters:
        com_port: Target serial port (e.g. "COM5" or "/dev/ttyUSB0").
        profile: The RelayConfiguration describing which sketch and relay
        configuration should be uploaded.
        progress_callback: Optional callable(percent: int, message: str)
            the GUI can supply to update its progress bar + console live
            during a real implementation. Not invoked with real progress
            in this phase.
    """

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

    # ------------------------------------------------------------------
    # Lifecycle stages -- each is a placeholder "hook" a subclass /
    # future implementation will fill in. Kept as separate methods (rather
    # than one big run()) so the GUI can report fine-grained progress.
    # ------------------------------------------------------------------

    def prepare(self) -> bool:
        """
        PLACEHOLDER. Future implementation: locate the correct .ino source
        under firmware/<board>/<N>CH/, and (once FirmwareConfigurator is
        implemented in a later phase) ensure its AUTO GENERATED CONFIG
        block matches self.profile before compilation.
        """
        self._set_stage(UploadStage.PREPARING, "Preparing upload (placeholder)")
        return True

    def compile(self) -> bool:
        """
        PLACEHOLDER. Future implementation: invoke arduino-cli compile
        for the target board's FQBN, streaming stdout/stderr to the
        console panel via progress_callback.
        """
        self._set_stage(UploadStage.COMPILING, "Compiling firmware (placeholder)")
        return True

    def upload(self) -> bool:
        """
        PLACEHOLDER. Future implementation: invoke arduino-cli upload (or
        esptool.py write_flash for ESP32) targeting self.com_port.
        """
        self._set_stage(UploadStage.UPLOADING, "Uploading firmware (placeholder)")
        return True

    def run(self) -> bool:
        """
        Convenience method that runs the full placeholder pipeline in
        order. Real implementations should still allow each stage to be
        called independently (e.g. for a "compile only / verify" mode).
        """
        logger.info(
            "%s.run() called for %s on %s (placeholder, no real flashing occurs)",
            type(self).__name__,
            self.profile.board,
            self.com_port,
        )
        if not self.prepare():
            self._set_stage(UploadStage.FAILED, "Preparation failed")
            return False
        if not self.compile():
            self._set_stage(UploadStage.FAILED, "Compilation failed")
            return False
        if not self.upload():
            self._set_stage(UploadStage.FAILED, "Upload failed")
            return False

        self._set_stage(UploadStage.SUCCESS, "Upload complete (placeholder)")
        return True

    # ------------------------------------------------------------------
    def _set_stage(self, stage: UploadStage, message: str) -> None:
        self.stage = stage
        logger.info("[%s] %s: %s", type(self).__name__, STAGE_LABELS[stage], message)
        if self.progress_callback:
            # Placeholder progress percentages just mark stage boundaries.
            percent_by_stage = {
                UploadStage.PREPARING: 10,
                UploadStage.COMPILING: 50,
                UploadStage.UPLOADING: 80,
                UploadStage.SUCCESS: 100,
                UploadStage.FAILED: 0,
            }
            self.progress_callback(percent_by_stage.get(stage, 0), message)


class ArduinoUploader(BaseUploader):
    """
    PLACEHOLDER uploader for Arduino UNO/Nano targets.

    Future implementation will select the correct arduino-cli FQBN
    (e.g. "arduino:avr:uno" or "arduino:avr:nano") based on board
    detection results, and drive arduino-cli's compile/upload
    sub-commands via QProcess.
    """

    FQBN_PLACEHOLDER = "arduino:avr:uno"  # or arduino:avr:nano


class ESP32Uploader(BaseUploader):
    """
    PLACEHOLDER uploader for ESP32 targets.

    Future implementation will select the correct arduino-cli FQBN
    (e.g. "esp32:esp32:esp32") for compilation, and use esptool.py (or
    arduino-cli's built-in upload, which wraps esptool) for flashing,
    at the correct baud rate for the detected board.
    """

    FQBN_PLACEHOLDER = "esp32:esp32:esp32"
