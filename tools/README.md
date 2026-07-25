# tools/

Reserved for external command-line tools the application will shell out to
in a future phase:

- **arduino-cli** — compiles and uploads sketches for Arduino UNO/Nano and
  (via the ESP32 Espressif core) ESP32 boards.
- **esptool.py** — low-level ESP32 flashing, used either standalone or
  indirectly through arduino-cli's upload step.

Nothing in this folder is invoked yet — see `core/uploader.py` for the
placeholder classes that will eventually wrap these tools via `QProcess`,
and `core/board_detector.py` for the placeholder detection functions.

When implemented, this folder will likely hold either:
1. Setup/install scripts that fetch the correct arduino-cli / esptool
   binaries for the user's platform, or
2. The vendored binaries themselves (for a fully offline, single-exe
   distribution) — a decision to be made in a later phase.
