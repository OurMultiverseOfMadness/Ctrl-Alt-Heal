"""Time parsing utilities for natural language time input."""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Union, Optional

from ctrl_alt_heal.utils.constants import (
    FREQUENCY_TIME_MAPPINGS,
    TIME_FORMAT_12H_PATTERN,
)
from ctrl_alt_heal.utils.exceptions import TimeParsingError


def parse_natural_time_input(time_str: str) -> Optional[str]:
    """
    Parse natural time input to HH:MM format.

    Handles formats like:
    - "10am", "2pm", "8pm" (12-hour format)
    - "10:30am", "2:30pm" (12-hour format with minutes)
    - "14:30", "23:59" (24-hour format)
    - "10:00", "20:00" (24-hour format)

    Args:
        time_str: Natural time input string

    Returns:
        Time in HH:MM format or None if invalid
    """
    if not time_str:
        return None

    time_str = time_str.lower().strip()

    # Handle 24-hour format (already in HH:MM)
    if ":" in time_str and ("am" not in time_str and "pm" not in time_str):
        try:
            # Validate it's a proper HH:MM format
            datetime.strptime(time_str, "%H:%M")
            return time_str
        except ValueError:
            return None

    # Handle 12-hour format with AM/PM
    pattern = TIME_FORMAT_12H_PATTERN
    match = re.match(pattern, time_str)

    if match:
        # Check that the entire string matches (no extra characters)
        if match.end() != len(time_str):
            return None

        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3)

        # Validate hour and minute
        if hour < 1 or hour > 12 or minute < 0 or minute > 59:
            return None

        # Convert to 24-hour format
        if period == "pm" and hour != 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute:02d}"

    return None


def parse_natural_times_input(times_input: Union[str, List[str]]) -> List[str]:
    """
    Parse natural times input to list of HH:MM format times.

    Handles:
    - Single time: "10am" -> ["10:00"]
    - Multiple times: ["10am", "2pm"] -> ["10:00", "14:00"]
    - Frequency text: "twice daily" -> ["08:00", "20:00"]
    - Mixed formats: ["10am", "14:30", "8pm"] -> ["10:00", "14:30", "20:00"]
    - Comma-separated string: "10am, 2pm, 8pm" -> ["10:00", "14:00", "20:00"]

    Args:
        times_input: Time input as string or list of strings

    Returns:
        List of times in HH:MM format
    """
    if not times_input:
        return ["08:00"]  # Default to morning

    # Convert string to list if needed
    if isinstance(times_input, str):
        # Check if it's a frequency description
        if times_input.lower() in FREQUENCY_TIME_MAPPINGS:
            return FREQUENCY_TIME_MAPPINGS[times_input.lower()]

        # Check if it's a comma-separated string
        if "," in times_input:
            time_strings = [t.strip() for t in times_input.split(",")]
            parsed_times = []
            for time_str in time_strings:
                parsed_time = parse_natural_time_input(time_str)
                if parsed_time:
                    parsed_times.append(parsed_time)
            return parsed_times if parsed_times else ["08:00"]

        # Try to parse as a single time
        parsed_time = parse_natural_time_input(times_input)
        return [parsed_time] if parsed_time else ["08:00"]

    # Handle list of times
    parsed_times = []
    for time_input in times_input:
        parsed_time = parse_natural_time_input(time_input)
        if parsed_time:
            parsed_times.append(parsed_time)

    # Return default if no valid times found
    return parsed_times if parsed_times else ["08:00"]


def parse_frequency_to_times(frequency: str) -> List[str]:
    """
    Parse frequency text to default times.

    Args:
        frequency: Frequency description (e.g., "twice daily", "morning", "evening")

    Returns:
        List of default times in HH:MM format
    """
    if not frequency:
        return ["08:00"]  # Default to morning

    frequency_lower = frequency.lower()
    times = []

    # Check for specific patterns
    if "morning" in frequency_lower:
        times.append("08:00")
    if "night" in frequency_lower or "evening" in frequency_lower:
        times.append("20:00")
    if "afternoon" in frequency_lower or "noon" in frequency_lower:
        times.append("12:00")

    # Handle "twice daily" or "2 times" patterns
    if ("twice" in frequency_lower or "2 " in frequency_lower) and len(times) == 0:
        times = ["08:00", "20:00"]
    elif (
        "thrice" in frequency_lower
        or "three" in frequency_lower
        or "3 " in frequency_lower
    ) and len(times) == 0:
        times = ["08:00", "14:00", "20:00"]
    elif ("four" in frequency_lower or "4 " in frequency_lower) and len(times) == 0:
        times = ["08:00", "12:00", "16:00", "20:00"]

    # If no times found, default to morning
    if not times:
        times = ["08:00"]

    return times


def validate_time_format(time_str: str) -> bool:
    """
    Validate if a time string is in proper HH:MM format.

    Args:
        time_str: Time string to validate

    Returns:
        True if valid, False otherwise
    """
    if not time_str:
        return False

    # Check for proper HH:MM format
    if not re.match(r"^\d{2}:\d{2}$", time_str):
        return False

    try:
        hour, minute = map(int, time_str.split(":"))
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except (ValueError, AttributeError):
        return False


def validate_time_range(time_str: str) -> bool:
    """
    Validate if a time is within valid range (00:00 to 23:59).

    Args:
        time_str: Time string to validate

    Returns:
        True if within valid range, False otherwise
    """
    if not validate_time_format(time_str):
        return False

    try:
        hour, minute = map(int, time_str.split(":"))
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except (ValueError, AttributeError):
        return False


def normalize_time_format(time_str: str) -> str:
    """
    Normalize time string to HH:MM format.

    Args:
        time_str: Time string to normalize

    Returns:
        Normalized time string or original if invalid
    """
    parsed = parse_natural_time_input(time_str)
    return parsed if parsed else time_str


def parse_natural_time_input_with_exception(time_str: str) -> str:
    """
    Parse natural time input to HH:MM format with exception handling.

    Handles formats like:
    - "10am", "2pm", "8pm" (12-hour format)
    - "10:30am", "2:30pm" (12-hour format with minutes)
    - "14:30", "23:59" (24-hour format)
    - "10:00", "20:00" (24-hour format)

    Args:
        time_str: Natural time input string

    Returns:
        Time in HH:MM format

    Raises:
        TimeParsingError: If time format is invalid
    """
    if not time_str:
        raise TimeParsingError("Time input cannot be empty", time_str)

    if not isinstance(time_str, str):
        raise TimeParsingError("Time input must be a string", time_str)

    time_str = time_str.lower().strip()

    # Handle 24-hour format (already in HH:MM)
    if ":" in time_str and ("am" not in time_str and "pm" not in time_str):
        try:
            # Validate it's a proper HH:MM format
            datetime.strptime(time_str, "%H:%M")
            return time_str
        except ValueError:
            raise TimeParsingError(f"Invalid 24-hour time format: {time_str}", time_str)

    # Handle 12-hour format with AM/PM
    pattern = TIME_FORMAT_12H_PATTERN
    match = re.match(pattern, time_str)

    if match:
        # Check that the entire string matches (no extra characters)
        if match.end() != len(time_str):
            raise TimeParsingError(f"Invalid time format: {time_str}", time_str)

        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3)

        # Validate hour and minute
        if hour < 1 or hour > 12 or minute < 0 or minute > 59:
            raise TimeParsingError(
                f"Invalid hour or minute values: {time_str}", time_str
            )

        # Convert to 24-hour format
        if period == "pm" and hour != 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute:02d}"

    raise TimeParsingError(f"Unrecognized time format: {time_str}", time_str)
