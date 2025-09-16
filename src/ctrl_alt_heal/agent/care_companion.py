from __future__ import annotations

import logging
import os
import boto3
from functools import lru_cache
from typing import Any

from strands import Agent
from strands.models.bedrock import BedrockModel

from ctrl_alt_heal.domain.models import ConversationHistory
from ctrl_alt_heal.tools.calendar_tool import calendar_ics_tool
from ctrl_alt_heal.tools.fhir_data_tool import fhir_data_tool
from ctrl_alt_heal.tools.image_description_tool import describe_image_tool
from ctrl_alt_heal.tools.search_tool import search_tool
from ctrl_alt_heal.tools.prescription_extraction_tool import (
    prescription_extraction_tool,
)
from ctrl_alt_heal.tools.user_profile_tool import (
    get_user_profile_tool,
    save_user_notes_tool,
    update_user_profile_tool,
)
from ctrl_alt_heal.tools.identity_tool import (
    find_user_by_identity_tool,
    create_user_with_identity_tool,
    get_or_create_user_tool,
)
from ctrl_alt_heal.tools.timezone_tool import (
    detect_user_timezone_tool,
    suggest_timezone_from_language_tool,
    auto_detect_timezone_tool,
)
from ctrl_alt_heal.tools.medication_schedule_tool import (
    auto_schedule_medication_tool,
    set_medication_schedule_tool,
    get_medication_schedule_tool,
    clear_medication_schedule_tool,
    get_user_prescriptions_tool,
    show_all_medications_tool,
)
from ctrl_alt_heal.tools.medication_ics_tool import (
    generate_medication_ics_tool,
    generate_single_medication_ics_tool,
)
from ctrl_alt_heal.interface.telegram_sender import send_telegram_file
from datetime import datetime
from strands import tool


from ctrl_alt_heal.domain.models import User

s3 = boto3.client("s3")

# Global variable to store chat_id for file sending
_current_chat_id = None


def set_chat_id_for_file_sending(chat_id: str):
    """Set the chat ID for automatic file sending in tool wrappers."""
    global _current_chat_id
    logger = logging.getLogger(__name__)
    logger.info(f"DEBUG: Setting _current_chat_id to {chat_id}")
    _current_chat_id = chat_id


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
def wrapped_generate_medication_ics_tool(
    user_id: str,
    prescription_name: str | None = None,
    reminder_minutes: int = 15,
    include_notes: bool = True,
):
    """Wrapper that automatically sends ICS files via Telegram."""
    global _current_chat_id
    logger = logging.getLogger(__name__)

    logger.info(f"DEBUG: _current_chat_id = {_current_chat_id}")

    # Call the original tool
    result = generate_medication_ics_tool(
        user_id=user_id,
        prescription_name=prescription_name,
        reminder_minutes=reminder_minutes,
        include_notes=include_notes,
    )

    logger.info(f"DEBUG: Result from generate_medication_ics_tool: {result}")

    # If successful and we have ICS content, send it via Telegram
    if (
        result.get("status") == "success"
        and result.get("ics_content")
        and _current_chat_id
    ):
        try:
            ics_content = result["ics_content"]
            filename = (
                f"medication_reminders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
            )
            caption = result.get(
                "message", "Here's your medication reminder calendar file!"
            )

            logger.info(f"Auto-sending ICS file to chat {_current_chat_id}: {filename}")
            send_telegram_file(_current_chat_id, ics_content, filename, caption)
            logger.info("Successfully auto-sent ICS file")

            # Update the result message to indicate file was sent and no further action needed
            result["message"] = (
                "✅ ICS calendar file generated and sent successfully! "
                f"The file contains {result.get('events_created', 0)} reminder events for your medications. "
                "You can import this into any calendar app (Google Calendar, Apple Calendar, Outlook, etc.). "
                "Each reminder will show 15 minutes before it's time to take your medication."
            )

        except Exception as e:
            logger.error(f"Failed to auto-send ICS file: {e}")

    return result


@tool(
    name="generate_single_medication_ics",
    description=(
        "Generates an ICS calendar file for a single medication with custom times. "
        "Use this when creating calendar events for a specific medication. "
        "Example triggers: 'Create a calendar for this medication', "
        "'Generate reminders for my morning pills'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "medication_name": {
                "type": "string",
                "description": "Name of the medication to create calendar for",
            },
            "times": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of times in user's timezone. Accepts natural formats like ['10am', '2pm', '8pm'] or HH:MM format like ['10:00', '14:00', '20:00']",
            },
            "duration_days": {
                "type": "integer",
                "description": "Number of days to create events for (default: 30)",
            },
            "dosage": {
                "type": "string",
                "description": "Dosage information to include in calendar events",
            },
            "reminder_minutes": {
                "type": "integer",
                "description": "Minutes before medication time to show reminder (default: 15)",
            },
        },
        "required": ["user_id", "medication_name", "times"],
    },
)
def wrapped_generate_single_medication_ics_tool(
    user_id: str,
    medication_name: str,
    times: list[str],
    duration_days: int = 30,
    dosage: str | None = None,
    reminder_minutes: int = 15,
):
    """Wrapper that automatically sends single medication ICS files via Telegram."""
    global _current_chat_id
    logger = logging.getLogger(__name__)

    # Call the original tool
    result = generate_single_medication_ics_tool(
        user_id=user_id,
        medication_name=medication_name,
        times=times,
        duration_days=duration_days,
        dosage=dosage,
        reminder_minutes=reminder_minutes,
    )

    # If successful and we have ICS content, send it via Telegram
    if (
        result.get("status") == "success"
        and result.get("ics_content")
        and _current_chat_id
    ):
        try:
            ics_content = result["ics_content"]
            medication_name = result.get("medication_name", "medication")
            filename = f"{medication_name.replace(' ', '_')}_reminders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
            caption = result.get(
                "message", f"Here's your calendar file for {medication_name}!"
            )

            logger.info(
                f"Auto-sending single ICS file to chat {_current_chat_id}: {filename}"
            )
            send_telegram_file(_current_chat_id, ics_content, filename, caption)
            logger.info("Successfully auto-sent single ICS file")

            # Update the result message to indicate file was sent and no further action needed
            result["message"] = (
                f"✅ ICS calendar file for {medication_name} generated and sent successfully! "
                f"The file contains {result.get('events_created', 0)} reminder events. "
                "You can import this into any calendar app (Google Calendar, Apple Calendar, Outlook, etc.). "
                "Each reminder will show 15 minutes before it's time to take your medication."
            )

        except Exception as e:
            logger.error(f"Failed to auto-send single ICS file: {e}")

    return result


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
                "description": "List of times in user's timezone. Accepts natural formats like ['10am', '2pm', '8pm'] or HH:MM format like ['10:00', '14:00', '20:00']",
            },
            "duration_days": {
                "type": "integer",
                "description": "Number of days to set the schedule for (default: 30)",
            },
        },
        "required": ["user_id", "prescription_name", "times"],
    },
)
def wrapped_set_medication_schedule_tool(
    user_id: str, prescription_name: str, times: list[str], duration_days: int = 30
):
    """Wrapper that automatically sends ICS files when medication schedules are created."""
    global _current_chat_id
    logger = logging.getLogger(__name__)

    # Call the original tool
    result = set_medication_schedule_tool(
        user_id=user_id,
        prescription_name=prescription_name,
        times=times,
        duration_days=duration_days,
    )

    # If successful and we have ICS content, send it via Telegram
    if (
        result.get("status") == "success"
        and result.get("ics_content")
        and _current_chat_id
    ):
        try:
            ics_content = result["ics_content"]
            medication_name = result.get("prescription_name", "medication")
            filename = result.get(
                "ics_filename",
                f"{medication_name.replace(' ', '_')}_schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics",
            )
            caption = result.get(
                "ics_caption", f"Calendar reminders for {medication_name}"
            )

            logger.info(
                f"Auto-sending schedule ICS file to chat {_current_chat_id}: {filename}"
            )
            send_telegram_file(_current_chat_id, ics_content, filename, caption)
            logger.info("Successfully auto-sent schedule ICS file")

            # Update the result message to indicate file was sent
            result["message"] = (
                result["message"] + " The calendar file has been sent to you!"
            )

        except Exception as e:
            logger.error(f"Failed to auto-send schedule ICS file: {e}")

    return result


@tool(
    name="auto_schedule_medication",
    description=(
        "Automatically creates medication schedules with default times based on prescription frequency. "
        "Use this when user wants to set up reminders but hasn't specified exact times. "
        "Example triggers: 'Set up medication reminders', 'Create schedules for my medications', "
        "'I want reminders for all my pills'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "prescription_name": {
                "type": "string",
                "description": "Name of the medication to schedule",
            },
            "duration_days": {
                "type": "integer",
                "description": "Number of days to set the schedule for (default: 30)",
            },
        },
        "required": ["user_id", "prescription_name"],
    },
)
def wrapped_auto_schedule_medication_tool(
    user_id: str, prescription_name: str, duration_days: int = 30
):
    """Wrapper that automatically sends ICS files when auto-schedules are created."""
    global _current_chat_id
    logger = logging.getLogger(__name__)

    # Call the original tool
    result = auto_schedule_medication_tool(
        user_id=user_id,
        prescription_name=prescription_name,
        duration_days=duration_days,
    )

    # If successful and we have ICS content, send it via Telegram
    if (
        result.get("status") == "success"
        and result.get("ics_content")
        and _current_chat_id
    ):
        try:
            ics_content = result["ics_content"]
            medication_name = result.get("prescription_name", "medication")
            filename = result.get(
                "ics_filename",
                f"{medication_name.replace(' ', '_')}_auto_schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics",
            )
            caption = result.get(
                "ics_caption",
                f"Auto-generated calendar reminders for {medication_name}",
            )

            logger.info(
                f"Auto-sending auto-schedule ICS file to chat {_current_chat_id}: {filename}"
            )
            send_telegram_file(_current_chat_id, ics_content, filename, caption)
            logger.info("Successfully auto-sent auto-schedule ICS file")

            # Update the result message to indicate file was sent
            result["message"] = (
                result["message"] + " The calendar file has been sent to you!"
            )

        except Exception as e:
            logger.error(f"Failed to auto-send auto-schedule ICS file: {e}")

    return result


@lru_cache(maxsize=1)
def get_system_prompt() -> str:
    """
    Fetches the system prompt from S3.
    The result is cached in memory for the lifetime of the Lambda container.
    """
    bucket = os.environ.get("ASSETS_BUCKET_NAME")
    if not bucket:
        raise ValueError("ASSETS_BUCKET_NAME environment variable not found.")
    key = "system_prompt.txt"
    response = s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read().decode("utf-8")


def get_agent(
    user: User, conversation_history: ConversationHistory | None = None
) -> Agent | Any:
    """Returns a new agent instance on every invocation."""
    import os

    # Check if we should use mock mode for local development
    use_mock = (
        os.getenv("LOCAL_DEVELOPMENT", "false").lower() == "true"
        or os.getenv("MOCK_AWS_SERVICES", "false").lower() == "true"
    )

    if use_mock:
        logger = logging.getLogger(__name__)
        logger.info("Using mock agent for local development")
        from ctrl_alt_heal.agent.mock_agent import get_mock_agent

        return get_mock_agent(user, conversation_history)

    base_system_prompt = get_system_prompt()

    # Enhance system prompt with user context and notes
    user_context = f"User context: user_id={user.user_id}, first_name='{user.first_name}', last_name='{user.last_name}', username='{user.username}'"

    system_prompt_parts = [base_system_prompt, user_context]

    if user.notes:
        system_prompt_parts.append(f"Important notes about this user: {user.notes}")

    system_prompt = "\n\n".join(system_prompt_parts)

    logger = logging.getLogger(__name__)
    # tools_list = [
    #     describe_image_tool,
    #     prescription_extraction_tool,
    #     fhir_data_tool,
    #     calendar_ics_tool,
    #     search_tool,
    #     update_user_profile_tool,
    #     get_user_profile_tool,
    #     save_user_notes_tool,
    #     find_user_by_identity_tool,
    #     create_user_with_identity_tool,
    #     get_or_create_user_tool,
    #     detect_user_timezone_tool,
    #     suggest_timezone_from_language_tool,
    #     auto_detect_timezone_tool,
    #     wrapped_auto_schedule_medication_tool,
    #     wrapped_set_medication_schedule_tool,
    #     get_medication_schedule_tool,
    #     clear_medication_schedule_tool,
    #     get_user_prescriptions_tool,
    #     show_all_medications_tool,
    #     wrapped_generate_medication_ics_tool,
    #     wrapped_generate_single_medication_ics_tool,
    # ]

    messages = []

    # Add the optimized conversation history
    if conversation_history:
        from ctrl_alt_heal.utils.history_management import (
            get_optimized_history_for_agent,
            analyze_history_usage,
        )

        # Log history analysis for debugging
        analysis = analyze_history_usage(conversation_history)
        logger.info(
            f"History analysis: {analysis['message_count']} messages, {analysis['estimated_tokens']} tokens, {analysis['token_usage_percentage']:.1f}% usage"
        )

        # Get optimized history for agent
        messages = get_optimized_history_for_agent(conversation_history)

    # Create a bedrock model instance
    bedrock_model = BedrockModel(
        model_id="apac.amazon.nova-lite-v1:0",
        region_name="ap-southeast-1",
        streaming=False,
    )

    agent = Agent(
        model=bedrock_model,
        system_prompt=system_prompt,
        messages=messages,  # type: ignore
        tools=[
            describe_image_tool,
            prescription_extraction_tool,
            fhir_data_tool,
            calendar_ics_tool,
            search_tool,
            update_user_profile_tool,
            get_user_profile_tool,
            save_user_notes_tool,
            find_user_by_identity_tool,
            create_user_with_identity_tool,
            get_or_create_user_tool,
            detect_user_timezone_tool,
            suggest_timezone_from_language_tool,
            auto_detect_timezone_tool,
            wrapped_auto_schedule_medication_tool,
            wrapped_set_medication_schedule_tool,
            get_medication_schedule_tool,
            clear_medication_schedule_tool,
            get_user_prescriptions_tool,
            show_all_medications_tool,
            wrapped_generate_medication_ics_tool,
            wrapped_generate_single_medication_ics_tool,
        ],
    )
    return agent
