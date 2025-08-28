"""Timezone utility functions for handling user-specific time operations."""

from __future__ import annotations

from datetime import datetime, UTC, timedelta
import zoneinfo

from ctrl_alt_heal.domain.models import User


def get_user_timezone(user: User) -> zoneinfo.ZoneInfo:
    """
    Get the user's timezone object, defaulting to UTC if not set.

    Args:
        user: User object with optional timezone field

    Returns:
        ZoneInfo object for the user's timezone
    """
    if user.timezone:
        try:
            return zoneinfo.ZoneInfo(user.timezone)
        except zoneinfo.ZoneInfoNotFoundError:
            # Fallback to UTC if timezone is invalid
            return zoneinfo.ZoneInfo("UTC")
    return zoneinfo.ZoneInfo("UTC")


def now_in_user_timezone(user: User) -> datetime:
    """
    Get the current datetime in the user's timezone.

    Args:
        user: User object with optional timezone field

    Returns:
        Current datetime in the user's timezone
    """
    user_tz = get_user_timezone(user)
    return datetime.now(UTC).astimezone(user_tz)


def format_time_for_user(
    dt: datetime, user: User, format_str: str = "%Y-%m-%d %H:%M:%S %Z"
) -> str:
    """
    Format a datetime object in the user's timezone.

    Args:
        dt: Datetime object (should be timezone-aware)
        user: User object with optional timezone field
        format_str: Python datetime format string

    Returns:
        Formatted datetime string in user's timezone
    """
    user_tz = get_user_timezone(user)

    # Ensure datetime is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    # Convert to user's timezone
    user_dt = dt.astimezone(user_tz)
    return user_dt.strftime(format_str)


def parse_user_time_to_utc(
    time_str: str, user: User, date_format: str = "%H:%M"
) -> datetime:
    """
    Parse a time string in the user's timezone and convert to UTC.

    Args:
        time_str: Time string (e.g., "14:30", "2:30 PM")
        user: User object with timezone information
        date_format: Format string for parsing the time

    Returns:
        Datetime object in UTC
    """
    user_tz = get_user_timezone(user)

    # Parse the time (assumes today's date)
    today = datetime.now(user_tz).date()
    naive_time = datetime.strptime(time_str, date_format).time()

    # Combine date and time in user's timezone
    user_dt = datetime.combine(today, naive_time)
    user_dt = user_dt.replace(tzinfo=user_tz)

    # Convert to UTC
    return user_dt.astimezone(UTC)


def get_friendly_timezone_name(timezone_str: str) -> str:
    """
    Convert a timezone string to a more user-friendly name.

    Args:
        timezone_str: Timezone identifier (e.g., "America/New_York")

    Returns:
        Friendly timezone name (e.g., "Eastern Time")
    """
    timezone_friendly_names = {
        "America/New_York": "Eastern Time",
        "America/Chicago": "Central Time",
        "America/Denver": "Mountain Time",
        "America/Los_Angeles": "Pacific Time",
        "Europe/London": "Greenwich Mean Time",
        "Europe/Paris": "Central European Time",
        "Europe/Berlin": "Central European Time",
        "Asia/Tokyo": "Japan Standard Time",
        "Asia/Shanghai": "China Standard Time",
        "Asia/Kolkata": "India Standard Time",
        "Asia/Singapore": "Singapore Time",
        "Australia/Sydney": "Australian Eastern Time",
        "UTC": "Coordinated Universal Time",
    }

    return timezone_friendly_names.get(timezone_str, timezone_str)


def create_user_calendar_event_times(
    user: User,
    start_time_str: str,
    duration_minutes: int = 60,
    date_str: str | None = None,
) -> tuple[str, str]:
    """
    Create calendar event start and end times in the user's timezone.

    Args:
        user: User object with timezone information
        start_time_str: Start time string (e.g., "14:30")
        duration_minutes: Event duration in minutes
        date_str: Optional date string (defaults to today)

    Returns:
        Tuple of (start_time_iso, end_time_iso) in RFC3339 format
    """
    user_tz = get_user_timezone(user)

    # Parse date or use today
    if date_str:
        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        event_date = datetime.now(user_tz).date()

    # Parse start time
    start_time = datetime.strptime(start_time_str, "%H:%M").time()

    # Create start datetime in user's timezone
    start_dt = datetime.combine(event_date, start_time)
    start_dt = start_dt.replace(tzinfo=user_tz)

    # Calculate end time
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    end_dt = end_dt.replace(tzinfo=user_tz)

    # Return in RFC3339 format
    return (start_dt.isoformat(), end_dt.isoformat())


def get_medication_schedule_times_utc(
    user: User, times_in_user_tz: list[str]
) -> list[str]:
    """
    Convert medication schedule times from user timezone to UTC for storage.

    Args:
        user: User object with timezone information
        times_in_user_tz: List of time strings in user's timezone (e.g., ["08:00", "20:00"])

    Returns:
        List of time strings in UTC format (e.g., ["13:00", "01:00"])
    """
    utc_times = []

    for time_str in times_in_user_tz:
        # Parse time in user's timezone
        user_dt = parse_user_time_to_utc(time_str, user)

        # Format as HH:MM in UTC
        utc_time_str = user_dt.strftime("%H:%M")
        utc_times.append(utc_time_str)

    return utc_times


def get_medication_schedule_times_user_tz(
    user: User, utc_times: list[str]
) -> list[str]:
    """
    Convert medication schedule times from UTC storage to user timezone for display.

    Args:
        user: User object with timezone information
        utc_times: List of time strings in UTC (e.g., ["13:00", "01:00"])

    Returns:
        List of time strings in user's timezone (e.g., ["08:00", "20:00"])
    """
    user_tz = get_user_timezone(user)
    user_times = []

    for utc_time_str in utc_times:
        # Parse UTC time
        utc_time = datetime.strptime(utc_time_str, "%H:%M").time()

        # Create UTC datetime (using today's date)
        today_utc = datetime.now(UTC).date()
        utc_dt = datetime.combine(today_utc, utc_time)
        utc_dt = utc_dt.replace(tzinfo=UTC)

        # Convert to user's timezone
        user_dt = utc_dt.astimezone(user_tz)

        # Format as HH:MM
        user_time_str = user_dt.strftime("%H:%M")
        user_times.append(user_time_str)

    return user_times
