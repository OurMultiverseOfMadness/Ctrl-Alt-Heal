"""Medication scheduling utilities for managing medication schedules."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from ctrl_alt_heal.domain.models import User
from ctrl_alt_heal.utils.time_parsing import parse_natural_times_input
from ctrl_alt_heal.utils.validation import (
    validate_medication_name,
    validate_schedule_times,
    validate_schedule_duration,
)


def create_medication_schedule(
    user: User, prescription: Dict[str, Any], times: List[str], duration: int
) -> Dict[str, Any]:
    """
    Create a medication schedule for a user.

    Args:
        user: User object
        prescription: Prescription data
        times: List of schedule times
        duration: Duration in days

    Returns:
        Schedule creation result
    """
    # Validate inputs
    if not validate_medication_name(prescription.get("name", "")):
        return {"status": "error", "message": "Invalid medication name"}

    if not validate_schedule_times(times):
        return {"status": "error", "message": "Invalid schedule times"}

    if not validate_schedule_duration(duration):
        return {"status": "error", "message": "Invalid duration (must be 1-365 days)"}

    # Parse and normalize times
    normalized_times = parse_natural_times_input(times)

    # Create schedule data
    schedule_data = {
        "user_id": user.user_id,
        "medication_name": prescription["name"],
        "dosage": prescription.get("dosage", ""),
        "frequency": prescription.get("frequency", ""),
        "schedule_times": normalized_times,
        "duration_days": duration,
        "start_date": datetime.now().isoformat(),
        "end_date": (datetime.now() + timedelta(days=duration)).isoformat(),
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    return {
        "status": "success",
        "message": f"Created schedule for {prescription['name']}",
        "schedule": schedule_data,
    }


def update_medication_schedule(
    user: User, prescription_id: str, times: List[str], duration: int
) -> Dict[str, Any]:
    """
    Update an existing medication schedule.

    Args:
        user: User object
        prescription_id: Prescription identifier
        times: New schedule times
        duration: New duration in days

    Returns:
        Schedule update result
    """
    # Validate inputs
    if not validate_schedule_times(times):
        return {"status": "error", "message": "Invalid schedule times"}

    if not validate_schedule_duration(duration):
        return {"status": "error", "message": "Invalid duration (must be 1-365 days)"}

    # Parse and normalize times
    normalized_times = parse_natural_times_input(times)

    # Update schedule data
    update_data = {
        "schedule_times": normalized_times,
        "duration_days": duration,
        "end_date": (datetime.now() + timedelta(days=duration)).isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    return {
        "status": "success",
        "message": f"Updated schedule for prescription {prescription_id}",
        "updates": update_data,
    }


def clear_medication_schedule(user: User, prescription_id: str) -> Dict[str, Any]:
    """
    Clear/disable a medication schedule.

    Args:
        user: User object
        prescription_id: Prescription identifier

    Returns:
        Schedule clearing result
    """
    update_data = {"status": "inactive", "updated_at": datetime.now().isoformat()}

    return {
        "status": "success",
        "message": f"Cleared schedule for prescription {prescription_id}",
        "updates": update_data,
    }


def get_medication_schedules(user: User) -> List[Dict[str, Any]]:
    """
    Get all medication schedules for a user.

    Args:
        user: User object

    Returns:
        List of medication schedules
    """
    # This would typically fetch from database
    # For now, return empty list as placeholder
    return []


def calculate_next_dose_time(
    schedule_times: List[str], user_timezone: str
) -> Optional[datetime]:
    """
    Calculate the next dose time based on schedule.

    Args:
        schedule_times: List of schedule times
        user_timezone: User's timezone

    Returns:
        Next dose datetime or None
    """
    if not schedule_times:
        return None

    try:
        import zoneinfo

        user_tz = zoneinfo.ZoneInfo(user_timezone)
        now = datetime.now(user_tz)

        # Find next dose time today
        for time_str in schedule_times:
            try:
                hour, minute = map(int, time_str.split(":"))
                dose_time = now.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

                if dose_time > now:
                    return dose_time
            except ValueError:
                continue

        # If no more doses today, return first dose tomorrow
        if schedule_times:
            try:
                hour, minute = map(int, schedule_times[0].split(":"))
                tomorrow = now + timedelta(days=1)
                return tomorrow.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
            except ValueError:
                pass

        return None
    except zoneinfo.ZoneInfoNotFoundError:
        return None


def format_schedule_for_display(schedule: Dict[str, Any]) -> str:
    """
    Format medication schedule for user display.

    Args:
        schedule: Schedule data

    Returns:
        Formatted schedule string
    """
    medication_name = schedule.get("medication_name", "Unknown Medication")
    dosage = schedule.get("dosage", "")
    times = schedule.get("schedule_times", [])
    frequency = schedule.get("frequency", "")

    # Format times
    if times:
        time_str = ", ".join(times)
    else:
        time_str = "No times specified"

    # Build display string
    display_parts = [f"**{medication_name}**"]

    if dosage:
        display_parts.append(f"Dosage: {dosage}")

    if frequency:
        display_parts.append(f"Frequency: {frequency}")

    display_parts.append(f"Times: {time_str}")

    return "\n".join(display_parts)


def check_schedule_conflicts(
    existing_schedules: List[Dict[str, Any]], new_times: List[str]
) -> List[str]:
    """
    Check for schedule conflicts with existing medications.

    Args:
        existing_schedules: List of existing schedules
        new_times: New schedule times

    Returns:
        List of conflict messages
    """
    conflicts = []

    for schedule in existing_schedules:
        existing_times = schedule.get("schedule_times", [])
        medication_name = schedule.get("medication_name", "Unknown")

        # Check for overlapping times (within 30 minutes)
        for new_time in new_times:
            for existing_time in existing_times:
                if _times_overlap(new_time, existing_time, 30):
                    conflicts.append(
                        f"Time conflict: {new_time} overlaps with {medication_name} at {existing_time}"
                    )

    return conflicts


def _times_overlap(time1: str, time2: str, tolerance_minutes: int = 30) -> bool:
    """
    Check if two times overlap within tolerance.

    Args:
        time1: First time in HH:MM format
        time2: Second time in HH:MM format
        tolerance_minutes: Tolerance in minutes

    Returns:
        True if times overlap within tolerance
    """
    try:
        hour1, minute1 = map(int, time1.split(":"))
        hour2, minute2 = map(int, time2.split(":"))

        # Convert to minutes since midnight
        minutes1 = hour1 * 60 + minute1
        minutes2 = hour2 * 60 + minute2

        # Check overlap
        return abs(minutes1 - minutes2) <= tolerance_minutes
    except (ValueError, AttributeError):
        return False


def generate_schedule_summary(schedules: List[Dict[str, Any]]) -> str:
    """
    Generate a summary of all medication schedules.

    Args:
        schedules: List of medication schedules

    Returns:
        Formatted summary string
    """
    if not schedules:
        return "No active medication schedules found."

    summary_parts = [f"You have {len(schedules)} active medication schedule(s):\n"]

    for i, schedule in enumerate(schedules, 1):
        summary_parts.append(f"{i}. {format_schedule_for_display(schedule)}")

    return "\n\n".join(summary_parts)
