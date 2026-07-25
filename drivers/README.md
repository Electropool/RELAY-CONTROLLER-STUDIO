# drivers/

Reserved for bundled USB-to-serial driver installers that a technician
without Arduino IDE experience may need before their OS recognizes a
connected board:

- **CH340 / CH341** drivers (common on low-cost Arduino UNO/Nano clones and
  many ESP32 dev boards).
- **CP2102 / CP210x** drivers (Silicon Labs — common on ESP32 DevKit V1
  boards, used by the firmware in `firmware/ESP32/`).
- **FTDI FT232** drivers (some genuine Arduino boards).

Nothing is bundled yet in this phase. A future phase may add a "Install
Drivers" button to the GUI that launches the appropriate installer from
this folder based on the detected (or selected) board.
