"""Tool for generating ICS calendar files for medication reminders."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta
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


@tool(
    name="generate_medication_ics",
    description=(
        "Generates an ICS calendar file for medication reminders that users can import "
        "into any calendar app. Creates recurring events for each medication schedule. "
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

        # Create events for each time
        for time_str in user_times:
            try:
                # Parse time
                time_obj = datetime.strptime(time_str, "%H:%M").time()

                # Create first event (today if time hasn't passed, tomorrow if it has)
                now_user = now_in_user_timezone(user)
                start_date = now_user.date()

                # If the time has already passed today, start tomorrow
                if time_obj <= now_user.time():
                    start_date = start_date + timedelta(days=1)

                # Create event
                event = Event()

                # Event title
                event_title = f"💊 Take {med['name']}"
                if include_notes and med["dosage"]:
                    event_title += f" ({med['dosage']})"

                event.name = event_title

                # Event timing (15-minute duration)
                start_datetime = datetime.combine(start_date, time_obj)
                start_datetime = start_datetime.replace(tzinfo=user_tz)
                end_datetime = start_datetime + timedelta(minutes=15)

                event.begin = start_datetime
                event.end = end_datetime

                # Event description
                description_parts = [f"Time to take your {med['name']}!"]
                if include_notes:
                    if med["dosage"]:
                        description_parts.append(f"Dosage: {med['dosage']}")
                    if med["frequency"]:
                        description_parts.append(f"Frequency: {med['frequency']}")

                description_parts.append(
                    "\n--- Created by Cara, your Care Companion ---"
                )
                event.description = "\n".join(description_parts)

                # Add reminder alarm
                if reminder_minutes > 0:
                    alarm = DisplayAlarm(trigger=timedelta(minutes=-reminder_minutes))
                    alarm.description = (
                        f"Take {med['name']} in {reminder_minutes} minutes"
                    )
                    event.alarms.append(alarm)

                # Create individual daily events instead of using RRULE (more compatible)
                base_event = event

                # Add the first event
                calendar.events.add(base_event)
                events_created += 1

                # Calculate remaining days until end date
                days_until_end = (end_date_user_tz - start_date).days

                # Create additional daily events
                for day_offset in range(1, min(days_until_end, 30)):
                    next_date = start_date + timedelta(days=day_offset)
                    if next_date > end_date_user_tz:
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
                            f"Take {med['name']} in {reminder_minutes} minutes"
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
            "message": "Failed to create calendar events. Please check your medication schedule times.",
        }

    # Generate ICS content
    ics_content = str(calendar)

    # Create summary message
    med_names = [med["name"] for med in scheduled_prescriptions]
    if len(med_names) == 1:
        summary_text = f"medication reminders for {med_names[0]}"
    else:
        summary_text = f"medication reminders for {len(med_names)} medications"

    return {
        "status": "success",
        "message": f"I've created a calendar file with {summary_text}! "
        f"The file contains {events_created} recurring reminder events. "
        f"You can import this into any calendar app (Google Calendar, Apple Calendar, Outlook, etc.). "
        f"Each reminder will show {reminder_minutes} minutes before it's time to take your medication.",
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
                "description": "List of times in user's timezone (e.g., ['08:00', '20:00'])",
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

    # Validate time format
    try:
        for time_str in times:
            datetime.strptime(time_str, "%H:%M")
    except ValueError:
        return {
            "status": "error",
            "message": "Please provide times in HH:MM format (24-hour), "
            "for example: ['08:00', '20:00'] for 8 AM and 8 PM.",
        }

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
    ics_content = str(calendar)

    times_display = ", ".join(times)

    return {
        "status": "success",
        "message": f"I've created a calendar file for {medication_name} with {events_created} daily reminders "
        f"at {times_display} ({user.timezone}) for the next {duration_days} days! "
        f"Each reminder will show {reminder_minutes} minutes before it's time to take your medication. "
        f"You can import this into any calendar app.",
        "ics_content": ics_content,
        "events_created": events_created,
        "medication_name": medication_name,
        "times": times,
        "duration_days": duration_days,
        "timezone": user.timezone,
    }
