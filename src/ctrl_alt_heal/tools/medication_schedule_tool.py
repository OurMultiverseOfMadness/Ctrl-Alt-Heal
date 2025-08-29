"""Tools for managing medication schedules with timezone awareness."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta

from strands import tool

from ctrl_alt_heal.infrastructure.prescriptions_store import PrescriptionsStore
from ctrl_alt_heal.infrastructure.users_store import UsersStore
from ctrl_alt_heal.utils.timezone_utils import (
    get_medication_schedule_times_utc,
    get_medication_schedule_times_user_tz,
    format_time_for_user,
    now_in_user_timezone,
)


@tool(
    name="set_medication_schedule",
    description=(
        "Sets a medication schedule with specific times in the user's timezone. "
        "Use this when a user wants to set reminder times for their medication. "
        "Example triggers: 'Remind me to take my medicine at 8 AM and 8 PM', "
        "'Set up a schedule for my medication', 'I want to take this twice daily at 9 and 21'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "prescription_name": {
                "type": "string",
                "description": "Name of the medication to schedule",
            },
            "times": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of times in user's timezone (e.g., ['08:00', '20:00', '14:30'])",
            },
            "duration_days": {
                "type": "integer",
                "description": "Number of days to set the schedule for (default: 30)",
            },
        },
        "required": ["user_id", "prescription_name", "times"],
    },
)
def set_medication_schedule_tool(
    user_id: str, prescription_name: str, times: list[str], duration_days: int = 30
) -> dict[str, Any]:
    """
    Sets a medication schedule for a specific prescription in the user's timezone.
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
            "message": "I need to know your timezone first. Could you tell me your timezone? "
            "(e.g., 'EST', 'Pacific Time', 'UTC+5', or a city like 'New York')",
            "needs_timezone": True,
        }

    # Find the prescription
    prescriptions = prescriptions_store.list_prescriptions(user_id, status="active")
    matching_prescription = None

    for prescription in prescriptions:
        if prescription_name.lower() in prescription.get("name", "").lower():
            matching_prescription = prescription
            break

    if not matching_prescription:
        # List available prescriptions for the user
        available_names = [p.get("name", "") for p in prescriptions if p.get("name")]
        if available_names:
            return {
                "status": "error",
                "message": f"I couldn't find a prescription for '{prescription_name}'. "
                f"Your active prescriptions are: {', '.join(available_names)}. "
                "Could you specify which one you'd like to schedule?",
            }
        else:
            return {
                "status": "error",
                "message": "I couldn't find any active prescriptions for you. "
                "Please add a prescription first before setting up a schedule.",
            }

    # Validate time format
    try:
        # Test parsing each time
        for time_str in times:
            datetime.strptime(time_str, "%H:%M")
    except ValueError:
        return {
            "status": "error",
            "message": "Please provide times in HH:MM format (24-hour), "
            "for example: ['08:00', '20:00'] for 8 AM and 8 PM.",
        }

    # Convert times to UTC for storage
    try:
        utc_times = get_medication_schedule_times_utc(user, times)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing times: {str(e)}. Please check your time format.",
        }

    # Calculate end date
    end_date = now_in_user_timezone(user) + timedelta(days=duration_days)
    until_iso = end_date.isoformat()

    # Set the schedule
    prescription_sk = matching_prescription["sk"]
    prescriptions_store.set_prescription_schedule(
        user_id=user_id,
        sk=prescription_sk,
        times_utc_hhmm=utc_times,
        until_iso=until_iso,
    )

    # Format confirmation message
    tz_name = user.timezone
    times_display = ", ".join(times)

    return {
        "status": "success",
        "message": f"Great! I've set up a schedule for {matching_prescription['name']} "
        f"at {times_display} ({tz_name}) for the next {duration_days} days. "
        f"You'll get reminders at these times each day.\n\n"
        f"💡 Tip: Would you like me to create a calendar file that you can import "
        f"into your phone's calendar app? Just ask me to 'generate calendar reminders' "
        f"or 'create an ICS file for my medications'.",
        "prescription_name": matching_prescription["name"],
        "times_user_tz": times,
        "timezone": tz_name,
        "duration_days": duration_days,
        "suggest_ics": True,
    }


@tool(
    name="get_medication_schedule",
    description=(
        "Gets the current medication schedule for a user, showing times in their timezone. "
        "Use this when a user asks about their current medication reminders or schedule. "
        "Example triggers: 'What's my medication schedule?', 'When do I take my pills?', "
        "'Show me my medication times'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "prescription_name": {
                "type": "string",
                "description": "Optional: specific medication name to check",
            },
        },
        "required": ["user_id"],
    },
)
def get_medication_schedule_tool(
    user_id: str, prescription_name: str | None = None
) -> dict[str, Any]:
    """
    Gets the medication schedule for a user, converting times to their timezone.
    """
    users_store = UsersStore()
    prescriptions_store = PrescriptionsStore()

    # Get user for timezone info
    user = users_store.get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found."}

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
            # Convert UTC times to user timezone
            if user.timezone:
                try:
                    user_times = get_medication_schedule_times_user_tz(
                        user, schedule_times
                    )
                except Exception:
                    # Fallback if timezone conversion fails
                    user_times = schedule_times
            else:
                user_times = schedule_times

            # Parse schedule end date
            try:
                until_date = datetime.fromisoformat(
                    schedule_until.replace("Z", "+00:00")
                )
                until_formatted = format_time_for_user(until_date, user, "%Y-%m-%d")
            except Exception:
                until_formatted = schedule_until

            scheduled_prescriptions.append(
                {
                    "name": prescription.get("name", ""),
                    "times": user_times,
                    "until": until_formatted,
                    "timezone": user.timezone or "UTC",
                }
            )

    if not scheduled_prescriptions:
        if prescription_name:
            return {
                "status": "info",
                "message": f"No schedule found for '{prescription_name}'. "
                "Would you like to set up a reminder schedule for this medication?",
            }
        else:
            return {
                "status": "info",
                "message": "You don't have any medication schedules set up yet. "
                "Would you like me to help you create reminder times for your medications?",
            }

    # Format response
    schedule_text = []
    for med in scheduled_prescriptions:
        times_str = ", ".join(med["times"])
        schedule_text.append(
            f"• {med['name']}: {times_str} ({med['timezone']}) until {med['until']}"
        )

    return {
        "status": "success",
        "message": "Here's your current medication schedule:\n\n"
        + "\n".join(schedule_text)
        + "\n\n💡 Want calendar reminders? I can create a calendar file that you can import "
        "into any calendar app. Just ask me to 'generate calendar reminders for my medications'!",
        "schedules": scheduled_prescriptions,
        "suggest_ics": True,
    }


@tool(
    name="clear_medication_schedule",
    description=(
        "Clears the medication schedule for a specific prescription. "
        "Use this when a user wants to stop or remove medication reminders. "
        "Example triggers: 'Stop reminding me about my medication', "
        "'Cancel my schedule for Metformin', 'Remove medication reminders'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "prescription_name": {
                "type": "string",
                "description": "Name of the medication to clear schedule for",
            },
        },
        "required": ["user_id", "prescription_name"],
    },
)
def clear_medication_schedule_tool(
    user_id: str, prescription_name: str
) -> dict[str, Any]:
    """
    Clears the medication schedule for a specific prescription.
    """
    prescriptions_store = PrescriptionsStore()

    # Find the prescription
    prescriptions = prescriptions_store.list_prescriptions(user_id, status="active")
    matching_prescription = None

    for prescription in prescriptions:
        if prescription_name.lower() in prescription.get("name", "").lower():
            matching_prescription = prescription
            break

    if not matching_prescription:
        available_names = [p.get("name", "") for p in prescriptions if p.get("name")]
        if available_names:
            return {
                "status": "error",
                "message": f"I couldn't find a prescription for '{prescription_name}'. "
                f"Your active prescriptions are: {', '.join(available_names)}.",
            }
        else:
            return {
                "status": "error",
                "message": "I couldn't find any active prescriptions for you.",
            }

    # Clear the schedule
    prescription_sk = matching_prescription["sk"]
    prescriptions_store.clear_prescription_schedule(user_id, prescription_sk)

    return {
        "status": "success",
        "message": f"I've cleared the medication schedule for {matching_prescription['name']}. "
        "You won't receive any more reminders for this medication.",
        "prescription_name": matching_prescription["name"],
    }


@tool(
    name="get_user_prescriptions",
    description=(
        "Gets all of the user's prescriptions (both scheduled and unscheduled). "
        "Use this when you need to see what medications the user has before setting up schedules. "
        "Example triggers: 'What prescriptions do I have?', 'Show me my medications', "
        "'What medicines am I taking?'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
        },
        "required": ["user_id"],
    },
)
def get_user_prescriptions_tool(user_id: str) -> dict[str, Any]:
    """
    Gets all of the user's prescriptions, showing which ones have schedules and which don't.
    """
    users_store = UsersStore()
    prescriptions_store = PrescriptionsStore()

    # Get user for timezone info
    user = users_store.get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found."}

    # Get all prescriptions
    prescriptions = prescriptions_store.list_prescriptions(user_id, status="active")

    if not prescriptions:
        return {
            "status": "info",
            "message": "You don't have any prescriptions on file yet. "
            "You can upload a prescription image or tell me about your medications.",
            "prescriptions": [],
            "scheduled_count": 0,
            "unscheduled_count": 0,
        }

    scheduled_prescriptions = []
    unscheduled_prescriptions = []

    for prescription in prescriptions:
        schedule_times = prescription.get("scheduleTimes")
        schedule_until = prescription.get("scheduleUntil")

        prescription_info = {
            "name": prescription.get("name", ""),
            "dosage": prescription.get("dosageText", ""),
            "frequency": prescription.get("frequencyText", ""),
            "status": prescription.get("status", ""),
        }

        # Debug logging to see what data we're getting
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Prescription data: {prescription}")
        logger.info(f"Extracted info: {prescription_info}")

        if schedule_times and schedule_until:
            # This prescription has a schedule
            if user.timezone:
                try:
                    user_times = get_medication_schedule_times_user_tz(
                        user, schedule_times
                    )
                except Exception:
                    user_times = schedule_times
            else:
                user_times = schedule_times

            prescription_info["schedule_times"] = user_times
            prescription_info["schedule_until"] = schedule_until
            prescription_info["timezone"] = user.timezone or "UTC"
            scheduled_prescriptions.append(prescription_info)
        else:
            # This prescription doesn't have a schedule
            unscheduled_prescriptions.append(prescription_info)

    # Format response with actual medication details
    if scheduled_prescriptions and unscheduled_prescriptions:
        message = f"I found {len(scheduled_prescriptions)} scheduled and {len(unscheduled_prescriptions)} unscheduled medications.\n\n"
        if unscheduled_prescriptions:
            message += "**Medications without schedules:**\n"
            for med in unscheduled_prescriptions[
                :5
            ]:  # Show first 5 to avoid too long messages
                message += f"• {med['name']} ({med['dosage']}) - {med['frequency']}\n"
            if len(unscheduled_prescriptions) > 5:
                message += f"... and {len(unscheduled_prescriptions) - 5} more\n"
            message += "\nWould you like me to help set up schedules for any of these?"
    elif scheduled_prescriptions:
        message = f"You have {len(scheduled_prescriptions)} medications with schedules set up:\n\n"
        for med in scheduled_prescriptions[:5]:
            times_str = ", ".join(med["schedule_times"])
            message += f"• {med['name']} ({med['dosage']}) - {times_str}\n"
        if len(scheduled_prescriptions) > 5:
            message += f"... and {len(scheduled_prescriptions) - 5} more\n"
        message += "\nWould you like to see all details or set up more schedules?"
    elif unscheduled_prescriptions:
        message = f"You have {len(unscheduled_prescriptions)} medications without schedules:\n\n"
        for med in unscheduled_prescriptions[
            :5
        ]:  # Show first 5 to avoid too long messages
            message += f"• {med['name']} ({med['dosage']}) - {med['frequency']}\n"
        if len(unscheduled_prescriptions) > 5:
            message += f"... and {len(unscheduled_prescriptions) - 5} more\n"
        message += "\nWould you like me to help you set up reminder times for any of these medications?"
    else:
        message = "You don't have any active prescriptions on file."

    return {
        "status": "success",
        "message": message,
        "prescriptions": prescriptions,
        "scheduled_prescriptions": scheduled_prescriptions,
        "unscheduled_prescriptions": unscheduled_prescriptions,
        "scheduled_count": len(scheduled_prescriptions),
        "unscheduled_count": len(unscheduled_prescriptions),
    }


@tool(
    name="show_all_medications",
    description=(
        "Shows all of the user's medications with full details. "
        "Use this when a user wants to see their complete medication list. "
        "Example triggers: 'Show me all my medications', 'List all my prescriptions', "
        "'What medications am I taking?'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
        },
        "required": ["user_id"],
    },
)
def show_all_medications_tool(user_id: str) -> dict[str, Any]:
    """
    Shows all of the user's medications with complete details.
    """
    users_store = UsersStore()
    prescriptions_store = PrescriptionsStore()

    # Get user for timezone info
    user = users_store.get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found."}

    # Get all prescriptions
    prescriptions = prescriptions_store.list_prescriptions(user_id, status="active")

    if not prescriptions:
        return {
            "status": "info",
            "message": "You don't have any prescriptions on file yet. "
            "You can upload a prescription image or tell me about your medications.",
            "prescriptions": [],
        }

    # Format complete medication list
    message = "**Your Complete Medication List:**\n\n"

    for i, prescription in enumerate(prescriptions, 1):
        name = prescription.get("name", "")
        dosage = prescription.get("dosageText", "")
        frequency = prescription.get("frequencyText", "")
        status = prescription.get("status", "")

        schedule_times = prescription.get("scheduleTimes")
        schedule_until = prescription.get("scheduleUntil")

        message += f"**{i}. {name}**\n"
        message += f"   Dosage: {dosage}\n"
        message += f"   Frequency: {frequency}\n"
        message += f"   Status: {status}\n"

        if schedule_times and schedule_until:
            if user.timezone:
                try:
                    user_times = get_medication_schedule_times_user_tz(
                        user, schedule_times
                    )
                    times_str = ", ".join(user_times)
                except Exception:
                    times_str = ", ".join(schedule_times)
            else:
                times_str = ", ".join(schedule_times)

            message += f"   Schedule: {times_str} until {schedule_until}\n"
        else:
            message += "   Schedule: No reminder schedule set\n"

        message += "\n"

    message += "Would you like me to help you set up reminder schedules for any medications that don't have them?"

    return {
        "status": "success",
        "message": message,
        "prescriptions": prescriptions,
        "total_count": len(prescriptions),
    }
