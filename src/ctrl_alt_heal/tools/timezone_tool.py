"""Tools for timezone detection and management."""

from __future__ import annotations

from typing import Any

from strands import tool

from ctrl_alt_heal.infrastructure.users_store import UsersStore
from ctrl_alt_heal.utils.timezone import (
    normalize_timezone_input as _normalize_timezone_input,
    suggest_timezone_from_language,
)


# Common timezone mappings for user-friendly input
TIMEZONE_MAPPINGS = {
    # US Timezones
    "est": "America/New_York",
    "eastern": "America/New_York",
    "et": "America/New_York",
    "cst": "America/Chicago",
    "central": "America/Chicago",
    "ct": "America/Chicago",
    "mst": "America/Denver",
    "mountain": "America/Denver",
    "mt": "America/Denver",
    "pst": "America/Los_Angeles",
    "pacific": "America/Los_Angeles",
    "pt": "America/Los_Angeles",
    # International
    "gmt": "Europe/London",
    "utc": "UTC",
    "bst": "Europe/London",  # British Summer Time
    "cet": "Europe/Paris",  # Central European Time
    "eet": "Europe/Kiev",  # Eastern European Time
    "jst": "Asia/Tokyo",  # Japan Standard Time
    "aest": "Australia/Sydney",  # Australian Eastern Standard Time
    "ist": "Asia/Kolkata",  # India Standard Time
    "cst_china": "Asia/Shanghai",  # China Standard Time
    "sgt": "Asia/Singapore",  # Singapore Time
    # Cities (common requests)
    "new york": "America/New_York",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "los angeles": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "singapore": "Asia/Singapore",
    "hong kong": "Asia/Hong_Kong",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
}


@tool(
    name="auto_detect_timezone",
    description=(
        "Automatically detects and suggests timezone based on user's language and proactively asks for confirmation. "
        "Use this when a new user starts the conversation and you want to set up their timezone proactively."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
        },
        "required": ["user_id"],
    },
)
def auto_detect_timezone_tool(user_id: str) -> dict[str, Any]:
    """
    Automatically detects and suggests timezone based on user's language.
    This is a proactive tool for new users.
    """
    users_store = UsersStore()
    user = users_store.get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found."}

    # If user already has timezone set, return it
    if user.timezone:
        return {
            "status": "success",
            "message": f"Your timezone is already set to: {user.timezone}",
            "timezone": user.timezone,
            "needs_timezone": False,
        }

    # If no language info, ask for timezone
    if not user.language:
        return {
            "status": "info",
            "message": "I'd like to set up your timezone for medication reminders. "
            "Could you tell me your timezone? You can say something like 'EST', 'Pacific Time', 'UTC+5', or your city name.",
            "needs_timezone": True,
        }

    # Use language to suggest timezone
    language_timezone_map = {
        "en": [
            "America/New_York",
            "America/Los_Angeles",
            "Europe/London",
            "Australia/Sydney",
        ],
        "es": [
            "America/Mexico_City",
            "Europe/Madrid",
            "America/Argentina/Buenos_Aires",
        ],
        "fr": ["Europe/Paris", "America/Montreal"],
        "de": ["Europe/Berlin", "Europe/Vienna", "Europe/Zurich"],
        "it": ["Europe/Rome"],
        "pt": ["America/Sao_Paulo", "Europe/Lisbon"],
        "ru": ["Europe/Moscow", "Asia/Yekaterinburg"],
        "zh": ["Asia/Shanghai", "Asia/Hong_Kong", "Asia/Taipei"],
        "ja": ["Asia/Tokyo"],
        "ko": ["Asia/Seoul"],
        "hi": ["Asia/Kolkata"],
        "ar": ["Asia/Riyadh", "Africa/Cairo"],
        "tr": ["Europe/Istanbul"],
        "nl": ["Europe/Amsterdam"],
        "sv": ["Europe/Stockholm"],
        "no": ["Europe/Oslo"],
        "da": ["Europe/Copenhagen"],
        "fi": ["Europe/Helsinki"],
        "pl": ["Europe/Warsaw"],
    }

    suggestions = language_timezone_map.get(user.language, [])

    if suggestions:
        # Auto-set the first suggestion as default
        default_timezone = suggestions[0]
        user.timezone = default_timezone
        users_store.upsert_user(user)

        return {
            "status": "success",
            "message": f"Based on your language ({user.language}), I've set your timezone to {default_timezone}. "
            f"If this is incorrect, you can tell me your actual timezone anytime.",
            "timezone": default_timezone,
            "needs_timezone": False,
            "auto_detected": True,
        }
    else:
        return {
            "status": "info",
            "message": "I'd like to set up your timezone for medication reminders. "
            "Could you tell me your timezone? You can say something like 'EST', 'Pacific Time', 'UTC+5', or your city name.",
            "needs_timezone": True,
        }


@tool(
    name="detect_user_timezone",
    description=(
        "Detects and sets the user's timezone. Use this when a user mentions their timezone, "
        "location, or when you need to know their timezone for scheduling. "
        "Example triggers: 'I'm in EST', 'My timezone is GMT+5', 'I live in New York', "
        "'What's my timezone?', 'Set my timezone to Pacific Time'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "timezone_input": {
                "type": "string",
                "description": "User's timezone input (e.g., 'EST', 'New York', 'UTC+5', 'Pacific')",
            },
        },
        "required": ["user_id"],
    },
)
def detect_user_timezone_tool(
    user_id: str, timezone_input: str | None = None
) -> dict[str, Any]:
    """
    Detects and sets the user's timezone based on their input.
    If no input provided, returns current timezone or prompts for it.
    """
    users_store = UsersStore()
    user = users_store.get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found."}

    # If no timezone input provided, check if user already has one set
    if not timezone_input:
        if user.timezone:
            return {
                "status": "success",
                "message": f"Your current timezone is set to: {user.timezone}",
                "timezone": user.timezone,
                "needs_timezone": False,
            }
        else:
            return {
                "status": "info",
                "message": "I don't have your timezone set yet. Could you tell me your timezone? "
                "You can say something like 'EST', 'Pacific Time', 'UTC+5', or your city name.",
                "timezone": None,
                "needs_timezone": True,
            }

    # Normalize and validate the timezone input
    normalized_timezone = _normalize_timezone_input(timezone_input)

    if not normalized_timezone:
        return {
            "status": "error",
            "message": f"I couldn't recognize the timezone '{timezone_input}'. "
            "Could you try something like 'EST', 'Pacific Time', 'UTC+5', or a city name like 'New York'?",
            "needs_timezone": True,
        }

    # Update user's timezone
    user.timezone = normalized_timezone
    users_store.upsert_user(user)

    return {
        "status": "success",
        "message": f"Great! I've set your timezone to {normalized_timezone}. "
        "I'll use this for all time-related features like medication schedules.",
        "timezone": normalized_timezone,
        "needs_timezone": False,
    }


@tool(
    name="suggest_timezone_from_language",
    description=(
        "Suggests likely timezones based on the user's language code from Telegram. "
        "Use this as a fallback when the user hasn't set a timezone and you need to make an educated guess."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
        },
        "required": ["user_id"],
    },
)
def suggest_timezone_from_language_tool(user_id: str) -> dict[str, Any]:
    """
    Suggests probable timezones based on the user's language code.
    This is a fallback method for timezone detection.
    """
    users_store = UsersStore()
    user = users_store.get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found."}

    language = user.language
    if not language:
        return {
            "status": "info",
            "message": "I don't have language information to suggest a timezone.",
            "suggestions": [],
        }

    # Use the utility function to get timezone suggestion
    suggested_timezone = suggest_timezone_from_language(language)
    suggestions = [suggested_timezone] if suggested_timezone else []

    if suggestions:
        return {
            "status": "success",
            "message": f"Based on your language ({language}), here are some likely timezones: {', '.join(suggestions)}. "
            "Could you tell me which one is correct, or provide your specific timezone?",
            "suggestions": suggestions,
            "language": language,
        }
    else:
        return {
            "status": "info",
            "message": "I couldn't suggest a timezone based on your language. "
            "Could you please tell me your timezone? (e.g., 'EST', 'UTC+5', 'New York')",
            "suggestions": [],
            "language": language,
        }
