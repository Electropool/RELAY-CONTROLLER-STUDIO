# Arduino UNO Timed Relay Sequencer

Firmware for driving animated sculptures, theme installations, exhibition
models, and other mechanical displays that need a repeating, timed sequence
of relay-driven outputs, with a live countdown shown on a 4-digit display.

Four ready-to-flash sketches are included, all built from the **same
architecture** — only the number of relay channels differs:

| Sketch                  | Relay Channels |
|--------------------------|:--------------:|
| `RelayController_2CH`    | 2              |
| `RelayController_4CH`    | 4              |
| `RelayController_8CH`    | 8              |
| `RelayController_16CH`   | 16             |

---

## 1. Hardware Requirements

- 1x Arduino UNO (ATmega328P)
- 1x TM1637 4-digit 7-segment display module
- 2 / 4 / 8 / 16x standard optocoupler relay modules (matching the sketch you flash)
- External power supply for the relay board(s) if driving mains-voltage loads
  (do **not** power multiple mains relays purely from the Arduino's 5V pin)

## 2. Library Requirements

Install via **Arduino IDE → Sketch → Include Library → Manage Libraries…**

- **TM1637Display** by Avishay Orpaz

## 3. Arduino IDE / Board Version

- Arduino IDE 1.8.19+ or Arduino IDE 2.x
- Board: **Arduino UNO**

## 4. Pin Diagram (default configuration)

### TM1637 Display (all sketches)

| TM1637 Pin | Arduino UNO Pin |
|------------|-----------------|
| CLK        | D2              |
| DIO        | D3              |
| VCC        | 5V              |
| GND        | GND             |

### Relay Channels — default pin assignment

| Relay # | 2CH | 4CH | 8CH | 16CH |
|--------:|:---:|:---:|:---:|:----:|
| 1  | D4 | D4 | D4  | D4  |
| 2  | D5 | D5 | D5  | D5  |
| 3  |    | D6 | D6  | D6  |
| 4  |    | D7 | D7  | D7  |
| 5  |    |    | D8  | D8  |
| 6  |    |    | D9  | D9  |
| 7  |    |    | D10 | D10 |
| 8  |    |    | D11 | D11 |
| 9  |    |    |     | D12 |
| 10 |    |    |     | D13 |
| 11 |    |    |     | A0  |
| 12 |    |    |     | A1  |
| 13 |    |    |     | A2  |
| 14 |    |    |     | A3  |
| 15 |    |    |     | A4  |
| 16 |    |    |     | A5  |

Pins D0/D1 (Serial) and D2/D3 (TM1637) are intentionally never used for
relays. On the 16CH build every remaining usable UNO digital/analog pin
(D4–D13, A0–A5) is used, which is the practical maximum for a single UNO.

Change any pin number in the `RelayPin[]` array at the top of each sketch if
your wiring differs — no other code needs to change.

## 5. Wiring Diagram (text form)

```
                +-------------------+
                |     Arduino UNO   |
                |                   |
   TM1637 CLK---| D2                |
   TM1637 DIO---| D3                |
                |                   |
   Relay 1 IN---| D4                |
   Relay 2 IN---| D5                |
   Relay 3 IN---| D6   (4CH+)       |
   Relay 4 IN---| D7   (4CH+)       |
   Relay 5 IN---| D8   (8CH+)       |
        ...     |  ...              |
   Relay16 IN---| A5   (16CH only)  |
                |                   |
                |  5V --- TM1637 VCC|
                |  GND--- TM1637 GND|
                |  GND--- Relay GND |
                +-------------------+

  Relay board VCC/JD-VCC: power from a supply appropriate for the number
  of relay coils being driven (5V for small boards, or an external 5V/12V
  supply for larger boards — check your relay module's specs).
```

## 6. User-Configurable Variables

All configuration lives at the **top of each `.ino` file**, before
`setup()`. Nothing else needs to be touched for normal use, and the section
is intentionally written as plain, flat variable declarations so that an
external tool (e.g. a companion Python GUI) can locate and rewrite these
values automatically before re-uploading the firmware.

```cpp
const uint8_t NUM_RELAYS = 4;                 // number of relay channels
unsigned long TOTAL_TIME_SECONDS = 30;        // full cycle length, in seconds
bool RELAY_ACTIVE_LOW = true;                 // true = active-LOW relay boards

const uint8_t TM1637_CLK_PIN = 2;
const uint8_t TM1637_DIO_PIN = 3;
uint8_t DISPLAY_BRIGHTNESS = 7;               // 0 (dim) ... 7 (bright)
bool COUNTDOWN_DISPLAY_ENABLED = true;

uint8_t RelayPin[NUM_RELAYS] = {4, 5, 6, 7};

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

Set both `RelayStartTime[i]` and `RelayStopTime[i]` to `0` to disable that
channel entirely:

- The relay is never turned on.
- It's fully ignored by the timing engine.
- It is exempt from startup validation (won't trigger an `Err`).

Example (4-channel board, channel 3 unused):

```cpp
unsigned long RelayStartTime[NUM_RELAYS] = {0, 0, 0, 12};
unsigned long RelayStopTime[NUM_RELAYS]  = {10, 20, 0, 18};
```

### Active-low vs. active-high relay boards

Most low-cost optocoupler relay boards are **active LOW** (pulling the input
LOW energizes the relay). If your board is active HIGH instead, just set:

```cpp
bool RELAY_ACTIVE_LOW = false;
```

Every relay output is automatically inverted — no other changes needed.

## 7. Error Checking

On every boot, `setup()` validates the configuration **before** starting the
sequence. If any of the following are true, the display shows `Err` and the
firmware halts permanently (all relays forced OFF; requires a power cycle
after fixing the configuration and re-uploading):

- `TOTAL_TIME_SECONDS < 1`
- Any **enabled** relay has `Start Time > Stop Time`
- Any **enabled** relay has `Stop Time > TOTAL_TIME_SECONDS`

Disabled relays (`Start == 0` and `Stop == 0`) are skipped by all three
checks.

## 8. Example Configuration (4-Channel board)

```
TOTAL_TIME_SECONDS = 30

Relay 1: Start = 0,  Stop = 10   (active)
Relay 2: Start = 0,  Stop = 20   (active)
Relay 3: Start = 8,  Stop = 25   (active)
Relay 4: Start = 12, Stop = 18   (active)
```

Countdown display: `30, 29, 28, ... 3, 2, 1, 0`, then repeats from `30`.

## 9. Design Notes

- No `delay()` calls anywhere — all scheduling uses `millis()`, so relay
  switching and the display stay responsive regardless of channel count.
- Code is organized into small, single-purpose helper functions
  (`shouldRelayBeOn`, `writeRelay`, `updateRelays`, `updateCountdownDisplay`,
  `validateConfiguration`, etc.) with no duplicated logic between them.
- The four sketches share an identical architecture; only `NUM_RELAYS`,
  the pin array, the timing arrays, and `TOTAL_TIME_SECONDS` differ between
  them, which keeps them simple to keep in sync and simple for an external
  tool to generate or edit.
