"""DateTime utilities for common datetime operations."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Optional


def get_current_utc_iso() -> str:
    """
    Get current UTC time as ISO format string.

    Returns:
        Current UTC time in ISO format
    """
    return datetime.now(UTC).isoformat()


def generate_timestamp_filename(prefix: str, suffix: str = "") -> str:
    """
    Generate a filename with timestamp.

    Args:
        prefix: Filename prefix
        suffix: Optional filename suffix

    Returns:
        Filename with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if suffix:
        return f"{prefix}_{timestamp}_{suffix}"
    return f"{prefix}_{timestamp}"


def format_datetime_for_display(
    dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Format datetime for user display.

    Args:
        dt: Datetime object to format
        format_str: Format string

    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def parse_iso_datetime(iso_str: str) -> Optional[datetime]:
    """
    Parse ISO format datetime string.

    Args:
        iso_str: ISO format datetime string

    Returns:
        Datetime object or None if invalid
    """
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def is_datetime_recent(dt: datetime, minutes: int = 30) -> bool:
    """
    Check if datetime is within recent time period.

    Args:
        dt: Datetime to check
        minutes: Minutes threshold

    Returns:
        True if datetime is within threshold
    """
    from datetime import timedelta

    return datetime.now(UTC) - dt < timedelta(minutes=minutes)


def get_time_difference_minutes(dt1: datetime, dt2: datetime) -> int:
    """
    Get time difference in minutes between two datetimes.

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        Time difference in minutes
    """
    return int((dt2 - dt1).total_seconds() / 60)
