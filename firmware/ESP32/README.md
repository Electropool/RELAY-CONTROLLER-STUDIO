# ESP32 DevKit V1 (ESP32-WROOM-32) Timed Relay Sequencer

Firmware for driving animated sculptures, theme installations, Durga Puja
theme installations, exhibition electronics, and other mechanical or
lighting displays that need a repeating, timed sequence of relay-driven
outputs, with a live countdown on a 4-digit display.

Four ready-to-flash sketches are included, all built on **exactly the same
software architecture** — configuration layout, timing engine, countdown
display, and validation/error logic are identical. Only the channel count
and the relay pin assignments differ.

| Sketch                  | Relay Channels | Output Method   |
|--------------------------|:--------------:|------------------|
| `RelayController_2CH`    | 2              | Direct GPIO      |
| `RelayController_4CH`    | 4              | Direct GPIO      |
| `RelayController_8CH`    | 8              | Direct GPIO      |
| `RelayController_16CH`   | 16             | Direct GPIO      |

**All four sketches use direct GPIO control only.** No GPIO expander IC of
any kind is used — no PCF8574, no MCP23017, nothing beyond the ESP32 board
itself, the TM1637 display, and the relay modules. This is possible on
ESP32 (unlike smaller boards such as the ESP8266) because the WROOM-32
module breaks out enough genuinely safe GPIOs to drive 16 channels directly.

---

## 1. Hardware Requirements

- 1x ESP32 DevKit V1 board (ESP32-WROOM-32)
- 1x TM1637 4-digit 7-segment display module
- 2 / 4 / 8 / 16x standard optocoupler relay modules (matching the sketch
  you flash)
- External power supply for the relay board(s) if driving mains-voltage
  loads (do not power multiple mains relays purely from the ESP32's 3V3/5V pin)

## 2. Library Requirements

Install via **Arduino IDE → Sketch → Include Library → Manage Libraries…**

- **TM1637Display** by Avishay Orpaz

## 3. Board Package / Arduino IDE Version

- Arduino IDE 1.8.19+ or Arduino IDE 2.x
- ESP32 board package **2.x or 3.x** by Espressif Systems (install via
  Boards Manager: search "esp32")
- Board selection: **"ESP32 Dev Module"**

## 4. GPIO Safety — Which Pins Are Safe on an ESP32-WROOM-32 DevKit

| GPIO(s)        | Role / Restriction                                             | Used in this project? |
|----------------|------------------------------------------------------------------|:----------------------:|
| GPIO34, 35, 36, 39 | Input-only — cannot drive an output at all                  | ❌ Never                |
| GPIO6–GPIO11   | Connected to the module's onboard SPI flash                     | ❌ Never                |
| GPIO1 (TX0), GPIO3 (RX0) | UART0 — used for flashing and the serial monitor       | ❌ Never                |
| GPIO0          | Boot/flash mode select strap — must be HIGH at reset             | ❌ Never                |
| GPIO12 (MTDI)  | Sets internal flash voltage at reset — wrong state can brick boot| ❌ Never                |
| GPIO2          | Strapping pin — "don't care" during normal boot (GPIO0 HIGH); only matters when simultaneously entering download mode | ⚠️ 16CH only, lowest priority |
| GPIO5          | Strapping pin — has an internal pull-up; only affects SDIO-slave boot timing, irrelevant for normal flash boot | ⚠️ 16CH only, lowest priority |
| GPIO15 (MTDO)  | Strapping pin — only affects whether the boot ROM log is printed | ⚠️ 16CH only, lowest priority |
| GPIO4, 13, 14, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33 | No boot role at all | ✅ Freely used |

**Design rule used to build the pin tables below:** relay pins are assigned
from a fixed priority list, safest pins first. GPIO2, GPIO5, and GPIO15 —
technically strapping pins, but only relevant to boot behavior in ways that
don't affect an already-flashed board's normal power-up — are used **only
on the 16-channel build**, and only after all 13 fully caution-free relay
pins have already been assigned. The 2CH, 4CH, and 8CH sketches never touch
them at all.

## 5. Pin Mapping Per Sketch

| Function          | 2CH  | 4CH  | 8CH  | 16CH |
|-------------------|:----:|:----:|:----:|:----:|
| TM1637 CLK        | 22   | 22   | 22   | 22   |
| TM1637 DIO        | 23   | 23   | 23   | 23   |
| Relay 1           | 4    | 4    | 4    | 4    |
| Relay 2           | 13   | 13   | 13   | 13   |
| Relay 3           |      | 14   | 14   | 14   |
| Relay 4           |      | 16   | 16   | 16   |
| Relay 5           |      |      | 17   | 17   |
| Relay 6           |      |      | 18   | 18   |
| Relay 7           |      |      | 19   | 19   |
| Relay 8           |      |      | 21   | 21   |
| Relay 9           |      |      |      | 25   |
| Relay 10          |      |      |      | 26   |
| Relay 11          |      |      |      | 27   |
| Relay 12          |      |      |      | 32   |
| Relay 13          |      |      |      | 33   |
| Relay 14          |      |      |      | 2 ⚠️ |
| Relay 15          |      |      |      | 5 ⚠️ |
| Relay 16          |      |      |      | 15 ⚠️ |

⚠️ = strapping pin, see the safety table above. Safe under normal operation;
only used because the 16-channel build needs every available GPIO.

All four sketches use the same GPIO for the TM1637 display, and every
lower-channel-count sketch's relay pins are a strict subset of the next
size up's — so wiring is consistent and predictable across the whole
product line.

## 6. Wiring Diagram

```
                    +---------------------------+
                    |   ESP32 DevKit V1          |
                    |   (ESP32-WROOM-32)         |
                    |                            |
   TM1637 CLK-------| GPIO22                     |
   TM1637 DIO-------| GPIO23                     |
                    |                            |
   Relay 1  IN------| GPIO4                      |
   Relay 2  IN------| GPIO13                     |
   Relay 3  IN------| GPIO14   (4CH+)            |
   Relay 4  IN------| GPIO16   (4CH+)            |
   Relay 5  IN------| GPIO17   (8CH+)            |
   Relay 6  IN------| GPIO18   (8CH+)            |
   Relay 7  IN------| GPIO19   (8CH+)            |
   Relay 8  IN------| GPIO21   (8CH+)            |
   Relay 9  IN------| GPIO25   (16CH only)       |
   Relay 10 IN------| GPIO26   (16CH only)       |
   Relay 11 IN------| GPIO27   (16CH only)       |
   Relay 12 IN------| GPIO32   (16CH only)       |
   Relay 13 IN------| GPIO33   (16CH only)       |
   Relay 14 IN------| GPIO2    (16CH only, ⚠️)    |
   Relay 15 IN------| GPIO5    (16CH only, ⚠️)    |
   Relay 16 IN------| GPIO15   (16CH only, ⚠️)    |
                    |                            |
                    | 3V3/5V --- TM1637 VCC      |
                    | GND ------ TM1637 GND      |
                    | GND ------ Relay board GND |
                    +---------------------------+

  Relay board VCC/JD-VCC: power from a supply appropriate for the number
  of relay coils being driven (many small boards run fine from the ESP32's
  5V pin for 2-4 relays; use an external 5V/12V supply for 8+ relays or
  mains-switching boards -- check your relay module's current draw).
```

## 7. User-Configurable Variables

All configuration lives between the `// ===== AUTO GENERATED CONFIG START
=====` and `// ===== AUTO GENERATED CONFIG END =====` markers near the top
of each `.ino` file. Nothing else needs to be touched for normal use, and
the section is written as plain, flat variable declarations so a companion
Python GUI can locate and rewrite these values automatically before
re-flashing.

```cpp
const uint8_t NUM_RELAYS = 4;
unsigned long TOTAL_TIME_SECONDS = 30;
bool RELAY_ACTIVE_LOW = true;

const uint8_t TM1637_CLK_PIN = 22;
const uint8_t TM1637_DIO_PIN = 23;
uint8_t DISPLAY_BRIGHTNESS = 7;
bool COUNTDOWN_DISPLAY_ENABLED = true;

uint8_t RelayPins[NUM_RELAYS] = {4, 13, 14, 16};

unsigned long RelayStartTime[NUM_RELAYS] = {0, 0, 8, 12};
unsigned long RelayStopTime[NUM_RELAYS]  = {10, 20, 25, 18};
```

### Relay timing rules

- A relay is **ON** whenever `RelayStartTime <= secondsElapsed < RelayStopTime`.
- Multiple relays may turn ON or OFF at exactly the same moment — each
  channel is evaluated independently every loop iteration.
- Times are whole seconds, measured from the start of the current cycle
  (i.e. from the moment the countdown display shows `TOTAL_TIME_SECONDS`).

### Disabling an unused channel

Set both `RelayStartTime[i]` and `RelayStopTime[i]` to `0` to mark that
channel as unused:

- The relay is never turned on.
- It's fully ignored by the timing engine.
- It never generates a validation error.

```
0, 0   -> Disabled  (never validated, never turned on)
0, 10  -> Valid
5, 0   -> Error     (Start > Stop)
15, 10 -> Error     (Start > Stop)
```

### Active-low vs. active-high relay boards

Most low-cost optocoupler relay boards are **active LOW** (pulling the
input LOW energizes the relay). If yours are active HIGH instead:

```cpp
bool RELAY_ACTIVE_LOW = false;
```

Every relay output is automatically inverted. No other changes needed.

## 8. Error Checking

On every boot, `setup()` validates the configuration **before** starting
the sequence and **before energizing any relay**. If any rule below is
broken, the display shows `Err`, every relay is forced OFF, and the
firmware halts permanently (power cycle required after fixing the
configuration and re-flashing):

- `TOTAL_TIME_SECONDS < 1`
- Any **enabled** relay has `Start Time > Stop Time`
- Any **enabled** relay has `Stop Time > TOTAL_TIME_SECONDS`

Disabled relays (`Start == 0` and `Stop == 0`) are skipped by all three
checks and can never trigger an error.

## 9. Example Configuration (4-Channel board)

```
TOTAL_TIME_SECONDS = 30

Relay 1: Start = 0,  Stop = 10   (active)
Relay 2: Start = 0,  Stop = 20   (active)
Relay 3: Start = 8,  Stop = 25   (active)
Relay 4: Start = 12, Stop = 18   (active)
```

Countdown display: `30, 29, 28, ... 3, 2, 1, 0`, then repeats from `30`.

## 10. Design Notes

- No `delay()` calls anywhere — all scheduling uses `millis()`. A `yield()`
  is called once per `loop()` pass (and inside the error halt loop) so the
  ESP32's background RTOS tasks and hardware watchdog stay serviced.
- Code is organized into small, single-purpose helper functions
  (`shouldRelayBeOn`, `writeRelay`, `updateRelays`, `updateCountdownDisplay`,
  `validateConfiguration`, etc.) with no duplicated logic between them.
- All four sketches share one identical template. `NUM_RELAYS`,
  `TOTAL_TIME_SECONDS`, `RelayPins[]`, `RelayStartTime[]`, and
  `RelayStopTime[]` are the only values that change between them — every
  other line of code, including the entire timing engine and validation
  logic, is byte-for-byte identical.
- Relay pins are assigned from one master priority list shared across all
  four sketches (fully-safe pins first, the three low-risk strapping pins
  last), so each smaller build's wiring is a strict subset of the next
  larger build's — a 4CH installation can be field-upgraded to 8CH wiring
  without moving any existing relay's wire.
