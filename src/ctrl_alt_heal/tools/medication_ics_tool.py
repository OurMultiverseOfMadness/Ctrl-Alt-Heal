"""Tool for generating ICS calendar files for medication reminders.

This tool intelligently groups medications with the same timing into single calendar events,
making it easier for users to manage multiple medications that need to be taken together.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from datetime import datetime, timedelta, date
from ics import Calendar, Event
from ics.alarm import DisplayAlarm

from strands import tool

from ctrl_alt_heal.infrastructure.prescriptions_store import PrescriptionsStore
from ctrl_alt_heal.infrastructure.users_store import UsersStore
from ctrl_alt_heal.utils.timezone_utils import (
    get_user_timezone,
    now_in_user_timezone,
    get_medication_schedule_times_user_tz,
)
from ctrl_alt_heal.utils.time_parsing import parse_natural_times_input
from ctrl_alt_heal.interface.telegram_sender import send_telegram_file
import logging

# Global variable to store chat_id for file sending
_current_chat_id = None


def set_chat_id_for_file_sending(chat_id: str):
    """Set the chat ID for automatic file sending in tools."""
    global _current_chat_id
    _current_chat_id = chat_id


# Use utility functions instead of duplicating time parsing logic
# _parse_natural_time_input -> parse_natural_time_input
# _parse_natural_times_input -> parse_natural_times_input


@tool(
    name="generate_medication_ics",
    description=(
        "Generates an ICS calendar file for medication reminders that users can import "
        "into any calendar app. Intelligently groups medications with the same timing "
        "into single events for convenience. Creates recurring events for each medication schedule. "
        "Example triggers: 'Create a calendar file for my medications', "
        "'Generate calendar reminders for my pills', 'Export my medication schedule to calendar'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "prescription_name": {
                "type": "string",
                "description": "Optional: specific medication to create calendar for",
            },
            "reminder_minutes": {
                "type": "integer",
                "description": "Minutes before medication time to show reminder (default: 15)",
            },
            "include_notes": {
                "type": "boolean",
                "description": "Include dosage and instructions in calendar event (default: true)",
            },
        },
        "required": ["user_id"],
    },
)
def generate_medication_ics_tool(
    user_id: str,
    prescription_name: str | None = None,
    reminder_minutes: int = 15,
    include_notes: bool = True,
) -> dict[str, Any]:
    """
    Generates an ICS calendar file for medication reminders.
    """
    users_store = UsersStore()
    prescriptions_store = PrescriptionsStore()

    # Get user for timezone info
    user = users_store.get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found."}

    if not user.timezone:
        return {
            "status": "error",
            "message": "I need to know your timezone first to create accurate calendar reminders. "
            "Could you tell me your timezone? (e.g., 'EST', 'Pacific Time', 'UTC+5')",
            "needs_timezone": True,
        }

    # Get prescriptions with schedules
    prescriptions = prescriptions_store.list_prescriptions(user_id, status="active")
    scheduled_prescriptions = []

    for prescription in prescriptions:
        # Skip if looking for specific prescription and this isn't it
        if (
            prescription_name
            and prescription_name.lower() not in prescription.get("name", "").lower()
        ):
            continue

        schedule_times = prescription.get("scheduleTimes")
        schedule_until = prescription.get("scheduleUntil")

        if schedule_times and schedule_until:
            scheduled_prescriptions.append(
                {
                    "name": prescription.get("name", ""),
                    "dosage": prescription.get("dosageText", ""),
                    "frequency": prescription.get("frequencyText", ""),
                    "schedule_times": schedule_times,
                    "schedule_until": schedule_until,
                }
            )

    if not scheduled_prescriptions:
        if prescription_name:
            return {
                "status": "error",
                "message": f"No schedule found for '{prescription_name}'. "
                "You need to set up a medication schedule first before creating calendar reminders.",
            }
        else:
            return {
                "status": "error",
                "message": "You don't have any medication schedules set up yet. "
                "Please set up medication reminder times first, then I can create a calendar file for you.",
            }

    # Create ICS calendar
    calendar = Calendar()
    calendar.creator = "Cara - Care Companion"
    user_tz = get_user_timezone(user)

    events_created = 0

    # First, collect all medications and their times to group them
    # This intelligent grouping creates single calendar events for medications
    # that need to be taken at the same time, reducing calendar clutter
    time_medications: Dict[
        str, List[Tuple[Dict[str, Any], date]]
    ] = {}  # time_str -> list of (med, end_date) tuples

    for med in scheduled_prescriptions:
        # Convert UTC times to user timezone for display
        try:
            user_times = get_medication_schedule_times_user_tz(
                user, med["schedule_times"]
            )
        except Exception:
            # Fallback if conversion fails
            user_times = med["schedule_times"]

        # Parse end date
        try:
            end_date = datetime.fromisoformat(
                med["schedule_until"].replace("Z", "+00:00")
            )
            end_date_user_tz = end_date.astimezone(user_tz).date()
        except Exception:
            # Default to 30 days from now if parsing fails
            end_date_user_tz = (now_in_user_timezone(user) + timedelta(days=30)).date()

        # Group this medication by its times
        for time_str in user_times:
            if time_str not in time_medications:
                time_medications[time_str] = []
            time_medications[time_str].append((med, end_date_user_tz))

    # Now create merged events for each time slot
    # Each time slot gets one event that lists all medications to take at that time
    for time_str, medications in time_medications.items():
        try:
            # Parse time
            time_obj = datetime.strptime(time_str, "%H:%M").time()

            # Create first event (today if time hasn't passed, tomorrow if it has)
            now_user = now_in_user_timezone(user)
            start_date = now_user.date()

            # If the time has already passed today, start tomorrow
            if time_obj <= now_user.time():
                start_date = start_date + timedelta(days=1)

            # Find the latest end date among all medications for this time
            latest_end_date = max(end_date for _, end_date in medications)

            # Calculate remaining days until end date
            days_until_end = (latest_end_date - start_date).days

            # Create events for each day
            for day_offset in range(min(days_until_end, 30)):
                event_date = start_date + timedelta(days=day_offset)
                if event_date > latest_end_date:
                    break

                # Create merged event
                event = Event()

                # Event title - show count if multiple medications
                if len(medications) == 1:
                    med, _ = medications[0]
                    event_title = f"💊 Take {med['name']}"
                    if include_notes and med["dosage"]:
                        event_title += f" ({med['dosage']})"
                else:
                    # Create a more descriptive title for combined medications
                    med_names = [med["name"] for med, _ in medications]
                    if len(med_names) <= 3:
                        event_title = f"💊 Take: {', '.join(med_names)}"
                    else:
                        event_title = f"💊 Take {len(medications)} medications"

                event.name = event_title

                # Event timing (15-minute duration)
                start_datetime = datetime.combine(event_date, time_obj)
                start_datetime = start_datetime.replace(tzinfo=user_tz)
                end_datetime = start_datetime + timedelta(minutes=15)

                event.begin = start_datetime
                event.end = end_datetime

                # Event description - list all medications
                description_parts = []
                if len(medications) == 1:
                    med, _ = medications[0]
                    description_parts.append(f"Time to take your {med['name']}!")
                    if include_notes:
                        if med["dosage"]:
                            description_parts.append(f"Dosage: {med['dosage']}")
                        if med["frequency"]:
                            description_parts.append(f"Frequency: {med['frequency']}")
                else:
                    description_parts.append(
                        f"Time to take {len(medications)} medications:"
                    )
                    for i, (med, _) in enumerate(medications, 1):
                        med_desc = f"{i}. {med['name']}"
                        if include_notes and med["dosage"]:
                            med_desc += f" - {med['dosage']}"
                        if include_notes and med["frequency"]:
                            med_desc += f" ({med['frequency']})"
                        description_parts.append(med_desc)

                    # Add a helpful note about combined reminders
                    if len(medications) > 1:
                        description_parts.append(
                            f"\n💡 All {len(medications)} medications are scheduled for the same time ({time_str}) "
                            "so you can take them together!"
                        )

                description_parts.append(
                    "\n--- Created by Cara, your Care Companion ---"
                )
                event.description = "\n".join(description_parts)

                # Add reminder alarm
                if reminder_minutes > 0:
                    alarm = DisplayAlarm(trigger=timedelta(minutes=-reminder_minutes))
                    if len(medications) == 1:
                        med, _ = medications[0]
                        alarm.description = (
                            f"Take {med['name']} in {reminder_minutes} minutes"
                        )
                    else:
                        # Create more descriptive alarm for combined medications
                        med_names = [med["name"] for med, _ in medications]
                        if len(med_names) <= 2:
                            alarm.description = f"Take {', '.join(med_names)} in {reminder_minutes} minutes"
                        else:
                            alarm.description = f"Take {len(medications)} medications in {reminder_minutes} minutes"
                    event.alarms.append(alarm)

                calendar.events.add(event)
                events_created += 1

        except Exception:
            # Skip this time if parsing fails
            continue

    if events_created == 0:
        return {
            "status": "error",
            "message": "Failed to create calendar events. Please check your medication schedule times.",
        }

    # Generate ICS content
    ics_content = calendar.serialize()

    # Create summary message
    med_names = [med["name"] for med in scheduled_prescriptions]
    if len(med_names) == 1:
        summary_text = f"medication reminders for {med_names[0]}"
    else:
        # Count unique time slots to show grouping benefit
        unique_times = len(time_medications)
        if unique_times < len(med_names):
            summary_text = f"medication reminders for {len(med_names)} medications (grouped into {unique_times} time slots)"
        else:
            summary_text = f"medication reminders for {len(med_names)} medications"

    # Auto-send the ICS file via Telegram
    logger = logging.getLogger(__name__)
    try:
        if _current_chat_id:
            filename = (
                f"medication_reminders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
            )
            caption = f"I've created a calendar file with {summary_text}! The file contains {events_created} recurring reminder events. Medications with the same timing are grouped together for convenience. You can import this into any calendar app."

            send_telegram_file(_current_chat_id, ics_content, filename, caption)

            # Update the message to indicate file was sent
            message = f"I've created a calendar file with {summary_text}! The file contains {events_created} recurring reminder events and has been sent to you. Medications with the same timing are grouped together for convenience. You can import this into any calendar app (Google Calendar, Apple Calendar, Outlook, etc.). Each reminder will show {reminder_minutes} minutes before it's time to take your medication."
        else:
            message = f"I've created a calendar file with {summary_text}! The file contains {events_created} recurring reminder events. Medications with the same timing are grouped together for convenience. You can import this into any calendar app (Google Calendar, Apple Calendar, Outlook, etc.). Each reminder will show {reminder_minutes} minutes before it's time to take your medication."

    except Exception as e:
        logger.error(f"Failed to auto-send ICS file: {e}")
        message = f"I've created a calendar file with {summary_text}! The file contains {events_created} recurring reminder events. Medications with the same timing are grouped together for convenience. You can import this into any calendar app (Google Calendar, Apple Calendar, Outlook, etc.). Each reminder will show {reminder_minutes} minutes before it's time to take your medication."

    return {
        "status": "success",
        "message": message,
        "ics_content": ics_content,
        "events_created": events_created,
        "medications": [med["name"] for med in scheduled_prescriptions],
        "timezone": user.timezone,
    }


@tool(
    name="generate_single_medication_ics",
    description=(
        "Generates an ICS calendar file for a specific medication with custom times. "
        "Use this when a user wants to create calendar reminders for a specific medication "
        "with specific times, without setting up the full medication schedule first. "
        "Note: For multiple medications, use 'generate_medication_ics' which automatically "
        "groups medications with the same timing into single events. "
        "Example triggers: 'Create calendar reminders for Metformin at 8 AM and 8 PM', "
        "'Make calendar events for my blood pressure medication'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "medication_name": {"type": "string"},
            "times": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of times in user's timezone. Accepts natural formats like ['10am', '2pm', '8pm'] or HH:MM format like ['10:00', '14:00', '20:00']",
            },
            "duration_days": {
                "type": "integer",
                "description": "Number of days to create reminders for (default: 30)",
            },
            "dosage": {
                "type": "string",
                "description": "Optional dosage information to include in reminders",
            },
            "reminder_minutes": {
                "type": "integer",
                "description": "Minutes before medication time to show reminder (default: 15)",
            },
        },
        "required": ["user_id", "medication_name", "times"],
    },
)
def generate_single_medication_ics_tool(
    user_id: str,
    medication_name: str,
    times: list[str],
    duration_days: int = 30,
    dosage: str | None = None,
    reminder_minutes: int = 15,
) -> dict[str, Any]:
    """
    Generates an ICS calendar file for a single medication with custom times.
    """
    users_store = UsersStore()

    # Get user for timezone info
    user = users_store.get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found."}

    if not user.timezone:
        return {
            "status": "error",
            "message": "I need to know your timezone first. Could you tell me your timezone? "
            "(e.g., 'EST', 'Pacific Time', 'UTC+5')",
            "needs_timezone": True,
        }

    # Parse and validate times (supports natural formats like "10am", "2pm", "8pm")
    parsed_times = parse_natural_times_input(times)

    if not parsed_times:
        return {
            "status": "error",
            "message": "Please provide times in a valid format. Examples: "
            "['10am', '2pm', '8pm'] or ['10:00', '14:00', '20:00'] or '10am, 2pm, 8pm'",
        }

    # Use parsed times
    times = parsed_times

    # Create ICS calendar
    calendar = Calendar()
    calendar.creator = "Cara - Care Companion"
    user_tz = get_user_timezone(user)

    events_created = 0
    now_user = now_in_user_timezone(user)
    end_date = (now_user + timedelta(days=duration_days)).date()

    # Create events for each time
    for time_str in times:
        try:
            # Parse time
            time_obj = datetime.strptime(time_str, "%H:%M").time()

            # Create first event (today if time hasn't passed, tomorrow if it has)
            start_date = now_user.date()
            if time_obj <= now_user.time():
                start_date = start_date + timedelta(days=1)

            # Create event
            event = Event()

            # Event title
            event_title = f"💊 Take {medication_name}"
            if dosage:
                event_title += f" ({dosage})"

            event.name = event_title

            # Event timing (15-minute duration)
            start_datetime = datetime.combine(start_date, time_obj)
            start_datetime = start_datetime.replace(tzinfo=user_tz)
            end_datetime = start_datetime + timedelta(minutes=15)

            event.begin = start_datetime
            event.end = end_datetime

            # Event description
            description_parts = [f"Time to take your {medication_name}!"]
            if dosage:
                description_parts.append(f"Dosage: {dosage}")

            description_parts.append(
                f"Reminder scheduled at {time_str} ({user.timezone})"
            )
            description_parts.append("\n--- Created by Cara, your Care Companion ---")
            event.description = "\n".join(description_parts)

            # Add reminder alarm
            if reminder_minutes > 0:
                alarm = DisplayAlarm(trigger=timedelta(minutes=-reminder_minutes))
                alarm.description = (
                    f"Take {medication_name} in {reminder_minutes} minutes"
                )
                event.alarms.append(alarm)

            # Create individual daily events instead of using RRULE (more compatible)
            base_event = event

            # Add the first event
            calendar.events.add(base_event)
            events_created += 1

            # Create additional daily events
            for day_offset in range(1, duration_days):
                next_date = start_date + timedelta(days=day_offset)
                if next_date > end_date:
                    break

                # Create copy of event for next day
                next_event = Event()
                next_event.name = base_event.name
                next_event.description = base_event.description

                # Update timing for next day
                next_start = datetime.combine(next_date, time_obj)
                next_start = next_start.replace(tzinfo=user_tz)
                next_end = next_start + timedelta(minutes=15)

                next_event.begin = next_start
                next_event.end = next_end

                # Copy alarms
                if reminder_minutes > 0:
                    next_alarm = DisplayAlarm(
                        trigger=timedelta(minutes=-reminder_minutes)
                    )
                    next_alarm.description = (
                        f"Take {medication_name} in {reminder_minutes} minutes"
                    )
                    next_event.alarms.append(next_alarm)

                calendar.events.add(next_event)
                events_created += 1

            # Skip the regular calendar.events.add since we already added events above
            continue

        except Exception:
            # Skip this time if parsing fails
            continue

    if events_created == 0:
        return {
            "status": "error",
            "message": "Failed to create calendar events. Please check your time format.",
        }

    # Generate ICS content
    ics_content = calendar.serialize()

    times_display = ", ".join(times)

    # Auto-send the ICS file via Telegram
    logger = logging.getLogger(__name__)
    try:
        if _current_chat_id:
            filename = f"{medication_name.replace(' ', '_')}_reminders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
            caption = f"I've created a calendar file for {medication_name} with {events_created} daily reminders at {times_display} ({user.timezone}) for the next {duration_days} days!"

            send_telegram_file(_current_chat_id, ics_content, filename, caption)

            # Update the message to indicate file was sent
            message = f"I've created a calendar file for {medication_name} with {events_created} daily reminders at {times_display} ({user.timezone}) for the next {duration_days} days and has been sent to you! Each reminder will show {reminder_minutes} minutes before it's time to take your medication. You can import this into any calendar app."
        else:
            message = f"I've created a calendar file for {medication_name} with {events_created} daily reminders at {times_display} ({user.timezone}) for the next {duration_days} days! Each reminder will show {reminder_minutes} minutes before it's time to take your medication. You can import this into any calendar app."

    except Exception as e:
        logger.error(f"Failed to auto-send single ICS file: {e}")
        message = f"I've created a calendar file for {medication_name} with {events_created} daily reminders at {times_display} ({user.timezone}) for the next {duration_days} days! Each reminder will show {reminder_minutes} minutes before it's time to take your medication. You can import this into any calendar app."

    return {
        "status": "success",
        "message": message,
        "ics_content": ics_content,
        "events_created": events_created,
        "medication_name": medication_name,
        "times": times,
        "duration_days": duration_days,
        "timezone": user.timezone,
    }
