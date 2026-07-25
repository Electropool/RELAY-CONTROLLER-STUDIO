"""
validation_manager.py
================================================================================
ValidationEngine: Handles logic for validating FirmwareProfiles.
Keeps all validation logic separate from the GUI.
================================================================================
"""

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
    """
    Applies business rules to a FirmwareProfile and returns a ValidationResult.
    """
    
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
            if relay.start_time == 0 and relay.stop_time == 0:
                logger.info(f"Relay {relay.relay_number + 1} Disabled")
                continue # Rule 1: disabled, no error
                
            if relay.start_time < 0:
                errors.append(ValidationError(
                    field=f"relay_{relay.relay_number}_start",
                    message="Start Time cannot be less than 0."
                ))
            
            if relay.stop_time < 0:
                errors.append(ValidationError(
                    field=f"relay_{relay.relay_number}_stop",
                    message="Stop Time cannot be less than 0."
                ))
                
            if relay.start_time > relay.stop_time:
                errors.append(ValidationError(
                    field=f"relay_{relay.relay_number}_start",
                    message=f"Relay {relay.relay_number + 1} Start > Stop"
                ))
                
            if relay.stop_time > profile.loop_time:
                errors.append(ValidationError(
                    field=f"relay_{relay.relay_number}_stop",
                    message=f"Relay {relay.relay_number + 1} Stop exceeds Loop Time"
                ))

        result = ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
        
        if result.is_valid:
            logger.info("Validation Passed")
        else:
            logger.info("Validation Failed")
            
        return result
