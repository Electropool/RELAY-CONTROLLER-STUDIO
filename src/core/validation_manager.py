# """
# validation_manager.py
# ================================================================================
# ValidationEngine: Handles logic for validating FirmwareProfiles.
# Keeps all validation logic separate from the GUI.
# ================================================================================
# """

from dataclasses import dataclass
from typing import List

from core.models import RelayConfiguration
from core.logger import get_logger

logger = get_logger()


@dataclass
class ValidationError:
    field: str      # E.g., 'loop_time', 'relay_0_start'
    message: str


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError]


class ValidationManager:
    """Applies business rules to a FirmwareProfile and returns a ValidationResult."""

    def validate(self, profile: RelayConfiguration) -> ValidationResult:
        logger.info("Validation Started")
        errors: List[ValidationError] = []

        # Validate Loop Time
        if profile.loop_time < 1 or profile.loop_time > 9999:
            errors.append(ValidationError(
                field="loop_time",
                message="Loop Time must be at least 1 second and at most 9999 seconds."
            ))

        # Validate Relays
        for relay in profile.relay_list:
            # Sort events: non‑empty sorted by start time, empty ones at the end
            non_empty = [e for e in relay.events if not (e.start_time == 0 and e.stop_time == 0)]
            non_empty.sort(key=lambda e: e.start_time)
            empty = [e for e in relay.events if (e.start_time == 0 and e.stop_time == 0)]
            relay.events = non_empty + empty

            last_stop = 0
            for event_idx, event in enumerate(relay.events):
                # Skip disabled events (including fully zeroed legacy entries)
                if not event.enabled or (event.start_time == 0 and event.stop_time == 0):
                    continue

                # Legacy field naming: first event uses "relay_<n>_start"/"_stop"
                base = f"relay_{relay.relay_number}"
                if event_idx == 0:
                    start_field = f"{base}_start"
                    stop_field = f"{base}_stop"
                    osc_field = f"{base}_osc_period"
                else:
                    start_field = f"{base}_{event_idx}_start"
                    stop_field = f"{base}_{event_idx}_stop"
                    osc_field = f"{base}_{event_idx}_osc_period"

                # Basic bounds
                if event.start_time < 0:
                    errors.append(ValidationError(
                        field=start_field,
                        message=f"Relay {relay.relay_number + 1} Event {event_idx + 1} Start Time < 0"
                    ))
                if event.stop_time < 0:
                    errors.append(ValidationError(
                        field=stop_field,
                        message=f"Relay {relay.relay_number + 1} Event {event_idx + 1} Stop Time < 0"
                    ))
                if event.start_time >= event.stop_time:
                    errors.append(ValidationError(
                        field=start_field,
                        message=f"Relay {relay.relay_number + 1} Event {event_idx + 1} Start >= Stop"
                    ))
                if event.stop_time > profile.loop_time:
                    errors.append(ValidationError(
                        field=stop_field,
                        message=f"Relay {relay.relay_number + 1} Event {event_idx + 1} Stop exceeds Loop Time"
                    ))

                # Overlap check
                if event.start_time < last_stop:
                    errors.append(ValidationError(
                        field=start_field,
                        message=f"Relay {relay.relay_number + 1} Event {event_idx + 1} overlaps previous event"
                    ))

                # Oscillation checks
                if event.oscillate:
                    duration_ms = (event.stop_time - event.start_time) * 1000
                    if event.osc_period_ms < 10:
                        errors.append(ValidationError(
                            field=osc_field,
                            message=f"Relay {relay.relay_number + 1} Event {event_idx + 1} Oscillation Period must be >= 10 ms"
                        ))
                    elif event.osc_period_ms > duration_ms:
                        errors.append(ValidationError(
                            field=osc_field,
                            message=f"Relay {relay.relay_number + 1} Event {event_idx + 1} Oscillation Period exceeds event duration"
                        ))

                # Update last_stop if the interval is valid
                if event.start_time < event.stop_time:
                    last_stop = event.stop_time

        result = ValidationResult(is_valid=len(errors) == 0, errors=errors)
        if result.is_valid:
            logger.info("Validation Passed")
        else:
            logger.info("Validation Failed")
        return result
