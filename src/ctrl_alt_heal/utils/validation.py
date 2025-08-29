"""Validation utilities for user input and data validation."""

from __future__ import annotations

import re
from typing import Dict, List, Any
from dataclasses import dataclass

from ctrl_alt_heal.utils.time_parsing import validate_time_format, validate_time_range
from ctrl_alt_heal.utils.exceptions import ValidationError


@dataclass
class ValidationResult:
    """Result of validation operation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]


def validate_medication_name(name: str) -> bool:
    """
    Validate medication name.

    Args:
        name: Medication name to validate

    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False

    # Basic validation: non-empty, reasonable length, no dangerous characters
    if len(name.strip()) < 1 or len(name) > 200:
        return False

    # Check for potentially dangerous characters (basic sanitization)
    dangerous_pattern = r'[<>"\']'
    if re.search(dangerous_pattern, name):
        return False

    return True


def validate_schedule_times(times: List[str]) -> bool:
    """
    Validate medication schedule times.

    Args:
        times: List of time strings to validate

    Returns:
        True if all times are valid, False otherwise
    """
    if not times:
        return False

    for time_str in times:
        if not validate_time_format(time_str) or not validate_time_range(time_str):
            return False

    return True


def validate_schedule_duration(days: int) -> bool:
    """
    Validate medication schedule duration.

    Args:
        days: Duration in days

    Returns:
        True if valid, False otherwise
    """
    return isinstance(days, int) and 1 <= days <= 365


def validate_user_input(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate user input data.

    Args:
        data: User input data to validate

    Returns:
        ValidationResult with validation status and any errors/warnings
    """
    errors = []
    warnings = []

    # Validate required fields
    required_fields = ["user_id"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")

    # Validate user_id format
    if "user_id" in data and data["user_id"]:
        user_id = str(data["user_id"])
        if not re.match(r"^[a-zA-Z0-9_-]+$", user_id):
            errors.append("Invalid user_id format")

    # Validate timezone if present
    if "timezone" in data and data["timezone"]:
        from ctrl_alt_heal.utils.timezone import validate_timezone

        if not validate_timezone(data["timezone"]):
            errors.append("Invalid timezone format")

    # Validate medication name if present
    if "medication_name" in data and data["medication_name"]:
        if not validate_medication_name(data["medication_name"]):
            errors.append("Invalid medication name")

    # Validate schedule times if present
    if "schedule_times" in data and data["schedule_times"]:
        if not validate_schedule_times(data["schedule_times"]):
            errors.append("Invalid schedule times")

    # Validate duration if present
    if "duration_days" in data and data["duration_days"]:
        if not validate_schedule_duration(data["duration_days"]):
            errors.append("Invalid duration (must be 1-365 days)")

    # Add warnings for potential issues
    if "medication_name" in data and data["medication_name"]:
        name = data["medication_name"]
        if len(name) > 100:
            warnings.append("Medication name is quite long")
        if re.search(r"\d+", name):
            warnings.append("Medication name contains numbers - verify this is correct")

    if "schedule_times" in data and data["schedule_times"]:
        times = data["schedule_times"]
        if len(times) > 6:
            warnings.append("Many schedule times - verify this is correct")

        # Check for very frequent dosing
        if len(times) >= 4:
            warnings.append(
                "Frequent medication schedule - verify with healthcare provider"
            )

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_prescription_data(prescription: Dict[str, Any]) -> ValidationResult:
    """
    Validate prescription data.

    Args:
        prescription: Prescription data to validate

    Returns:
        ValidationResult with validation status and any errors/warnings
    """
    errors = []
    warnings = []

    # Validate required fields
    required_fields = ["name", "dosage", "frequency"]
    for field in required_fields:
        if field not in prescription or not prescription[field]:
            errors.append(f"Missing required prescription field: {field}")

    # Validate medication name
    if "name" in prescription and prescription["name"]:
        if not validate_medication_name(prescription["name"]):
            errors.append("Invalid medication name")

    # Validate dosage
    if "dosage" in prescription and prescription["dosage"]:
        dosage = str(prescription["dosage"])
        if len(dosage.strip()) < 1 or len(dosage) > 100:
            errors.append("Invalid dosage format")

    # Validate frequency
    if "frequency" in prescription and prescription["frequency"]:
        frequency = str(prescription["frequency"])
        if len(frequency.strip()) < 1 or len(frequency) > 100:
            errors.append("Invalid frequency format")

    # Validate duration if present
    if "duration_days" in prescription and prescription["duration_days"]:
        try:
            duration = int(prescription["duration_days"])
            if not validate_schedule_duration(duration):
                errors.append("Invalid duration (must be 1-365 days)")
        except (ValueError, TypeError):
            errors.append("Duration must be a number")

    # Add warnings for potential issues
    if "name" in prescription and prescription["name"]:
        name = prescription["name"]
        if len(name) > 80:
            warnings.append("Medication name is quite long")

    if "frequency" in prescription and prescription["frequency"]:
        frequency = prescription["frequency"].lower()
        if "as needed" in frequency or "prn" in frequency:
            warnings.append("As-needed medication - verify scheduling is appropriate")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def sanitize_user_input(input_str: str) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        input_str: User input string to sanitize

    Returns:
        Sanitized string
    """
    if not input_str:
        return ""

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', "", str(input_str))

    # Trim whitespace
    sanitized = sanitized.strip()

    return sanitized


def validate_email_format(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid email format, False otherwise
    """
    if not email:
        return False

    # Basic email validation pattern
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, email))


def validate_phone_format(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate

    Returns:
        True if valid phone format, False otherwise
    """
    if not phone:
        return False

    # Remove all non-digit characters
    digits_only = re.sub(r"\D", "", phone)

    # Check if it's a reasonable length (7-15 digits)
    return 7 <= len(digits_only) <= 15


# Exception-based validation functions
def validate_medication_name_with_exception(name: str) -> None:
    """
    Validate medication name and raise ValidationError if invalid.

    Args:
        name: Medication name to validate

    Raises:
        ValidationError: If medication name is invalid
    """
    if not name or not isinstance(name, str):
        raise ValidationError(
            "Medication name is required and must be a string", "medication_name", name
        )

    # Check length
    if len(name.strip()) < 1 or len(name) > 200:
        raise ValidationError(
            f"Medication name must be between 1 and 200 characters, got {len(name)}",
            "medication_name",
            name,
        )

    # Check for dangerous characters
    dangerous_pattern = r'[<>"\']'
    if re.search(dangerous_pattern, name):
        raise ValidationError(
            "Medication name contains dangerous characters", "medication_name", name
        )


def validate_schedule_times_with_exception(times: List[str]) -> None:
    """
    Validate medication schedule times and raise ValidationError if invalid.

    Args:
        times: List of time strings to validate

    Raises:
        ValidationError: If any time is invalid
    """
    if not times:
        raise ValidationError("Schedule times are required", "schedule_times", times)

    for i, time_str in enumerate(times):
        if not validate_time_format(time_str):
            raise ValidationError(
                f"Invalid time format at position {i}: {time_str}",
                "schedule_times",
                time_str,
            )
        if not validate_time_range(time_str):
            raise ValidationError(
                f"Invalid time range at position {i}: {time_str}",
                "schedule_times",
                time_str,
            )


def validate_schedule_duration_with_exception(days: int) -> None:
    """
    Validate medication schedule duration and raise ValidationError if invalid.

    Args:
        days: Duration in days

    Raises:
        ValidationError: If duration is invalid
    """
    if not isinstance(days, int):
        raise ValidationError("Duration must be an integer", "duration_days", days)

    if days < 1 or days > 365:
        raise ValidationError(
            f"Duration must be between 1 and 365 days, got {days}",
            "duration_days",
            days,
        )


def validate_user_id_with_exception(user_id: str) -> None:
    """
    Validate user ID and raise ValidationError if invalid.

    Args:
        user_id: User ID to validate

    Raises:
        ValidationError: If user ID is invalid
    """
    if not user_id or not isinstance(user_id, str):
        raise ValidationError(
            "User ID is required and must be a string", "user_id", user_id
        )

    if not re.match(r"^[a-zA-Z0-9_-]+$", user_id):
        raise ValidationError(
            "User ID contains invalid characters. Only letters, numbers, underscores, and hyphens are allowed",
            "user_id",
            user_id,
        )


def validate_prescription_data_with_exception(prescription: Dict[str, Any]) -> None:
    """
    Validate prescription data and raise ValidationError if invalid.

    Args:
        prescription: Prescription data to validate

    Raises:
        ValidationError: If prescription data is invalid
    """
    if not prescription or not isinstance(prescription, dict):
        raise ValidationError(
            "Prescription data is required and must be a dictionary",
            "prescription",
            prescription,
        )

    # Validate required fields
    required_fields = ["name", "dosage", "frequency"]
    for field in required_fields:
        if field not in prescription or not prescription[field]:
            raise ValidationError(
                f"Missing required prescription field: {field}",
                field,
                prescription.get(field),
            )

    # Validate medication name
    validate_medication_name_with_exception(prescription["name"])

    # Validate dosage
    dosage = prescription["dosage"]
    if not dosage or not isinstance(dosage, str):
        raise ValidationError(
            "Dosage is required and must be a string", "dosage", dosage
        )

    if len(dosage.strip()) < 1 or len(dosage) > 100:
        raise ValidationError(
            f"Dosage must be between 1 and 100 characters, got {len(dosage)}",
            "dosage",
            dosage,
        )

    # Validate frequency
    frequency = prescription["frequency"]
    if not frequency or not isinstance(frequency, str):
        raise ValidationError(
            "Frequency is required and must be a string", "frequency", frequency
        )

    if len(frequency.strip()) < 1 or len(frequency) > 100:
        raise ValidationError(
            f"Frequency must be between 1 and 100 characters, got {len(frequency)}",
            "frequency",
            frequency,
        )

    # Validate duration if present
    if "duration_days" in prescription and prescription["duration_days"]:
        try:
            duration = int(prescription["duration_days"])
            validate_schedule_duration_with_exception(duration)
        except (ValueError, TypeError):
            raise ValidationError(
                "Duration must be a number",
                "duration_days",
                prescription["duration_days"],
            )
