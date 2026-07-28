# User Guide

This guide explains how to configure and upload firmware using **Relay Controller Studio**.

---

# 1. Launch the Application

Open **Relay Controller Studio**.

On the first launch, the Startup Wizard will automatically install the required tools (Arduino CLI, board packages, and libraries).

Wait until the setup is complete.

---

# 2. Create a New Project

1. Click **New Project**.
2. Select your board:
   - Arduino UNO
   - Arduino Nano
   - ESP32
3. Select the relay variant:
   - 2 Channel
   - 4 Channel
   - 8 Channel
   - 16 Channel

---

# 3. Configure the Project

Set the global firmware options:

- Loop Time
- Relay Active Low / High
- Countdown Display
- Display Brightness

---

# 4. Configure Relay Events

For each relay, add one or more events.

Each event contains:

- Start Time
- Stop Time
- Oscillation (Optional)
- Oscillation Period (ms)

Use **0 / 0** to disable an event.

The Timeline updates automatically as you edit.

---

# 5. Save the Project

Click **Save Project** to store the configuration as a JSON file.

Saved projects can be reopened later using **Open Project**.

---

# 6. Connect Your Board

Connect your Arduino or ESP32 using a USB cable.

The software will automatically detect:

- Connected Board
- COM Port

If detection fails, select the board and COM port manually.

---

# 7. Upload Firmware

Click **Upload Firmware**.

The software will automatically:

1. Validate the configuration.
2. Generate the firmware.
3. Compile the firmware.
4. Upload it to the selected board.

Wait until **Upload Successful** is displayed.

---

# Troubleshooting

### Board not detected

- Check the USB cable.
- Install the correct USB driver.
- Verify the COM port.

### Validation failed

Correct the errors shown in the Validation Panel before uploading.

### Upload failed

- Close Arduino IDE or any software using the COM port.
- Reconnect the board.
- Try uploading again.

---

# Supported Boards

- Arduino UNO
- Arduino Nano
- ESP32 Dev Module

Supported relay variants:

- 2 Channel
- 4 Channel
- 8 Channel
- 16 Channel

---

For bug reports or feature requests, please open an Issue on the GitHub repository.
