/*
  ============================================================================
  RelayController_8CH
  ----------------------------------------------------------------------------
  Timed Relay Sequencer for Animated Sculptures / Theme Installations
  Board:    Arduino UNO
  Display:  TM1637 4-Digit 7-Segment Display (countdown timer)
  Outputs:  8 channel(s) of optocoupler relay modules
  ----------------------------------------------------------------------------
  DESCRIPTION
  This firmware repeatedly runs a fixed-length timed cycle (TOTAL_TIME_SECONDS
  long). Each relay channel has its own Start Time and Stop Time, expressed in
  whole seconds measured from the beginning of the cycle. On every pass through
  loop(), the firmware works out -- purely from elapsed time -- whether each
  relay should currently be ON or OFF, and drives the outputs accordingly.

  A TM1637 display continuously shows the number of seconds remaining in the
  current cycle, counting down from TOTAL_TIME_SECONDS to 0. When it reaches
  0 the cycle restarts automatically and the countdown begins again.

  No delay() calls are used anywhere in this sketch. All timing is handled
  with millis(), so the relays and the display are always updated on time
  regardless of how many channels are configured.
  ----------------------------------------------------------------------------
  CONFIGURATION
  Every value you are likely to need to change lives in the "USER
  CONFIGURATION" block below, before setup(). Nothing below that block should
  need to be edited for normal use. This makes the sketch easy to edit by
  hand, and also easy for an external tool (e.g. a companion Python GUI) to
  parse and rewrite automatically, since the configuration values sit in a
  single, predictable, well-labelled section at the top of the file.
  ----------------------------------------------------------------------------
  LIBRARY REQUIREMENTS
    - TM1637Display by Avishay Orpaz
      (Arduino IDE: Sketch > Include Library > Manage Libraries > "TM1637")
  ----------------------------------------------------------------------------
  ARDUINO VERSION
    - Arduino IDE 1.8.19+ or Arduino IDE 2.x
    - Target board: Arduino UNO (ATmega328P)
  ============================================================================
*/

#include <TM1637Display.h>

// ============================================================================
//                            USER CONFIGURATION
//  Everything an operator (human or automated GUI) should ever need to touch
//  lives in this block. Do not move timing logic out of here into loop().
// ============================================================================

// ---- Number of relay channels on this build -------------------------------
// This must match the number of entries in every array below.
const uint8_t NUM_RELAYS = 8;

// ---- Overall cycle length --------------------------------------------------
// The countdown display counts down from this value to 0, then the whole
// sequence (all relay timings) restarts from time 0 again.
unsigned long TOTAL_TIME_SECONDS = 45;

// ---- Relay electrical polarity ---------------------------------------------
// Many low-cost optocoupler relay boards energize the relay when the input
// pin is pulled LOW rather than HIGH. Set this once to match your hardware
// and every relay output in the sketch is automatically inverted for you.
//   true  = active LOW  relay boards  (LOW = relay ON,  HIGH = relay OFF)
//   false = active HIGH relay boards  (HIGH = relay ON, LOW  = relay OFF)
bool RELAY_ACTIVE_LOW = true;

// ---- TM1637 display wiring --------------------------------------------------
const uint8_t TM1637_CLK_PIN = 2;
const uint8_t TM1637_DIO_PIN = 3;

// ---- Display brightness (0 = dimmest ... 7 = brightest) --------------------
uint8_t DISPLAY_BRIGHTNESS = 7;

// ---- Countdown display enable ----------------------------------------------
// If false, the TM1637 display is cleared/blanked but the relay sequencing
// still runs normally in the background.
bool COUNTDOWN_DISPLAY_ENABLED = true;

// ---- Relay output pins ------------------------------------------------------
// One digital pin per relay channel. Index 0 corresponds to Relay 1, etc.
uint8_t RelayPin[NUM_RELAYS] = {4, 5, 6, 7, 8, 9, 10, 11};

// ---- Relay Events (Multiple Start/Stop timings with optional Oscillation) ----
struct RelayEvent {
  unsigned long startTime;
  unsigned long stopTime;
  bool oscillate;
  unsigned long oscPeriodMs;
};

const uint8_t MAX_EVENTS_PER_RELAY = 3;

RelayEvent relayEvents[NUM_RELAYS][MAX_EVENTS_PER_RELAY] = {
  { {0, 0, false, 1000}, {0, 0, false, 1000}, {0, 0, false, 1000} },
  { {0, 0, false, 1000}, {0, 0, false, 1000}, {0, 0, false, 1000} },
  { {0, 0, false, 1000}, {0, 0, false, 1000}, {0, 0, false, 1000} },
  { {0, 0, false, 1000}, {0, 0, false, 1000}, {0, 0, false, 1000} },
  { {0, 0, false, 1000}, {0, 0, false, 1000}, {0, 0, false, 1000} },
  { {0, 0, false, 1000}, {0, 0, false, 1000}, {0, 0, false, 1000} },
  { {0, 0, false, 1000}, {0, 0, false, 1000}, {0, 0, false, 1000} },
  { {0, 0, false, 1000}, {0, 0, false, 1000}, {0, 0, false, 1000} }
};

// ============================================================================
//                      END OF USER CONFIGURATION SECTION
//        Nothing below this line should need to change for normal use.
// ============================================================================


// ---- Display object ---------------------------------------------------------
TM1637Display display(TM1637_CLK_PIN, TM1637_DIO_PIN);

// ---- Cycle timing state -------------------------------------------------
unsigned long cycleStartMillis = 0;   // millis() timestamp of current cycle start
unsigned long lastDisplayedSecond = 0xFFFFFFFF; // forces first display refresh

// ============================================================================
// FUNCTION: relayIsDisabled
// Returns true if a relay channel is configured as disabled, i.e. both its
// start and stop times are exactly 0. Disabled relays are ignored entirely
// by the timing engine and are skipped during validation.
// ============================================================================
bool relayIsDisabled(uint8_t index) {
  for (uint8_t e = 0; e < MAX_EVENTS_PER_RELAY; e++) {
    if (relayEvents[index][e].startTime != 0 || relayEvents[index][e].stopTime != 0) {
      return false;
    }
  }
  return true;
}

// ============================================================================
// FUNCTION: writeRelay
// Drives a single relay output pin to the requested logical state (true =
// energized / ON, false = de-energized / OFF), automatically applying the
// RELAY_ACTIVE_LOW polarity setting so calling code never has to think about
// electrical polarity.
// ============================================================================
void writeRelay(uint8_t index, bool energized) {
  bool electricalLevel = RELAY_ACTIVE_LOW ? !energized : energized;
  digitalWrite(RelayPin[index], electricalLevel ? HIGH : LOW);
}

// ============================================================================
// FUNCTION: allRelaysOff
// Forces every relay output to the OFF (de-energized) state. Used at startup
// and whenever the firmware halts in the error state.
// ============================================================================
void allRelaysOff() {
  for (uint8_t i = 0; i < NUM_RELAYS; i++) {
    writeRelay(i, false);
  }
}

// ============================================================================
// FUNCTION: showError
// Displays "Err" on the TM1637 display, forces all relays OFF for safety, and
// halts the firmware permanently (infinite loop). Used when the startup
// configuration validation fails.
// ============================================================================
void showError() {
  allRelaysOff();
  const uint8_t errSegments[] = {
    SEG_A | SEG_F | SEG_E | SEG_D | SEG_G,               // 'E'
    SEG_E | SEG_G,                                       // 'r'
    SEG_E | SEG_G                                        // 'r'
  };
  display.setSegments(errSegments, 3, 1); // 3 characters, starting at position 1
  while (true) {
    // Halt here forever. A physical reset/power cycle is required after
    // fixing the configuration.
  }
}

// ============================================================================
// FUNCTION: validateConfiguration
// Checks every ENABLED relay channel's timing against the rules below and
// halts with an "Err" display if any rule is broken:
//   1) TOTAL_TIME_SECONDS must be >= 1
//   2) For each enabled relay: Start Time must not exceed Stop Time
//   3) For each enabled relay: Stop Time must not exceed TOTAL_TIME_SECONDS
// Disabled relays (Start == 0 and Stop == 0) are skipped entirely and never
// cause a validation failure.
// ============================================================================
void validateConfiguration() {
  if (TOTAL_TIME_SECONDS < 1) {
    showError();
  }

  for (uint8_t i = 0; i < NUM_RELAYS; i++) {
    if (relayIsDisabled(i)) {
      continue;
    }
    unsigned long lastStop = 0;
    for (uint8_t e = 0; e < MAX_EVENTS_PER_RELAY; e++) {
      unsigned long start = relayEvents[i][e].startTime;
      unsigned long stop = relayEvents[i][e].stopTime;
      if (start == 0 && stop == 0) {
        continue;
      }
      if (start > stop) {
        showError();
      }
      if (stop > TOTAL_TIME_SECONDS) {
        showError();
      }
      if (start < lastStop) {
        showError();
      }
      if (relayEvents[i][e].oscillate) {
        unsigned long oscPeriod = relayEvents[i][e].oscPeriodMs;
        unsigned long durationMs = (stop - start) * 1000UL;
        if (oscPeriod < 10 || oscPeriod > durationMs) {
          showError();
        }
      }
      lastStop = stop;
    }
  }
}

// ============================================================================
// FUNCTION: shouldRelayBeOn
// Determines whether a given relay channel should currently be energized,
// based purely on how many seconds have elapsed since the cycle began.
// Disabled channels always return false.
// ============================================================================
bool shouldRelayBeOn(uint8_t index, unsigned long secondsElapsed) {
  for (uint8_t e = 0; e < MAX_EVENTS_PER_RELAY; e++) {
    unsigned long start = relayEvents[index][e].startTime;
    unsigned long stop = relayEvents[index][e].stopTime;
    if (start == 0 && stop == 0) {
      continue;
    }
    if (secondsElapsed >= start && secondsElapsed < stop) {
      if (relayEvents[index][e].oscillate) {
        unsigned long currentMs = millis();
        unsigned long eventStartMs = cycleStartMillis + (start * 1000UL);
        unsigned long elapsedInEventMs = currentMs - eventStartMs;
        unsigned long period = relayEvents[index][e].oscPeriodMs;
        if (period < 10) period = 10;
        return (elapsedInEventMs / period) % 2 == 0;
      }
      return true;
    }
  }
  return false;
}

// ============================================================================
// FUNCTION: updateRelays
// Walks every relay channel and sets its output to match what the timing
// engine says it should be right now. Multiple relays can turn on or off in
// the very same call, since each one is evaluated independently against the
// same secondsElapsed value.
// ============================================================================
void updateRelays(unsigned long secondsElapsed) {
  for (uint8_t i = 0; i < NUM_RELAYS; i++) {
    bool desiredState = shouldRelayBeOn(i, secondsElapsed);
    writeRelay(i, desiredState);
  }
}

// ============================================================================
// FUNCTION: updateCountdownDisplay
// Refreshes the TM1637 display with the number of seconds remaining in the
// current cycle, but only rewrites the display when the value actually
// changes (avoids unnecessary I2C/bit-bang traffic every loop iteration).
// If COUNTDOWN_DISPLAY_ENABLED is false, the display is simply blanked once.
// ============================================================================
void updateCountdownDisplay(unsigned long secondsRemaining) {
  if (!COUNTDOWN_DISPLAY_ENABLED) {
    if (lastDisplayedSecond != 0) {
      display.clear();
      lastDisplayedSecond = 0;
    }
    return;
  }

  if (secondsRemaining != lastDisplayedSecond) {
    display.showNumberDec(secondsRemaining, false);
    lastDisplayedSecond = secondsRemaining;
  }
}

// ============================================================================
// SETUP
// ============================================================================
void setup() {
  // Configure every relay pin as an output and make sure nothing is
  // energized before we know the configuration is valid.
  for (uint8_t i = 0; i < NUM_RELAYS; i++) {
    pinMode(RelayPin[i], OUTPUT);
  }
  allRelaysOff();

  // Bring up the display before validation so that showError() can use it.
  display.setBrightness(DISPLAY_BRIGHTNESS);
  display.clear();

  // Halts forever (showing "Err") if the configuration is invalid.
  validateConfiguration();

  // Configuration is valid -- start the first cycle now.
  cycleStartMillis = millis();
}

// ============================================================================
// LOOP
// ============================================================================
void loop() {
  unsigned long now = millis();
  unsigned long elapsedMillis = now - cycleStartMillis;
  unsigned long secondsElapsed = elapsedMillis / 1000UL;

  // Has the current cycle finished? If so, restart it from time 0.
  if (secondsElapsed >= TOTAL_TIME_SECONDS) {
    cycleStartMillis = now;
    elapsedMillis = 0;
    secondsElapsed = 0;
  }

  // Drive every relay according to the current position in the cycle.
  updateRelays(secondsElapsed);

  // Refresh the countdown display (TOTAL_TIME_SECONDS down to 0).
  unsigned long secondsRemaining = TOTAL_TIME_SECONDS - secondsElapsed;
  updateCountdownDisplay(secondsRemaining);
}
