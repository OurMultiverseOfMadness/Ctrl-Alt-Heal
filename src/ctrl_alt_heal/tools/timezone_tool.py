"""Tools for timezone detection and management."""

from __future__ import annotations

from typing import Any
import re

from strands import tool

from ctrl_alt_heal.infrastructure.users_store import UsersStore


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


def _normalize_timezone_input(timezone_input: str) -> str | None:
    """
    Normalizes user timezone input to a standard timezone identifier.

    Args:
        timezone_input: User's timezone input (e.g., "EST", "New York", "UTC+5")

    Returns:
        Standardized timezone identifier or None if not recognized
    """
    if not timezone_input:
        return None

    # Clean the input
    normalized = timezone_input.lower().strip()

    # Direct mapping lookup
    if normalized in TIMEZONE_MAPPINGS:
        return TIMEZONE_MAPPINGS[normalized]

    # Handle UTC offset formats like "UTC+5", "GMT-8", "+0530"
    utc_pattern = r"(utc|gmt)?\s*([+-]?\d{1,2}):?(\d{2})?"
    match = re.match(utc_pattern, normalized)
    if match:
        sign_hour = match.group(2)

        # Parse the offset
        try:
            if sign_hour.startswith(("+", "-")):
                sign = sign_hour[0]
                hour = int(sign_hour[1:])
            else:
                sign = "+" if int(sign_hour) >= 0 else "-"
                hour = abs(int(sign_hour))

            # Format as Etc/GMT offset (note: Etc/GMT uses inverted signs)
            if sign == "+":
                return f"Etc/GMT-{hour}"
            else:
                return f"Etc/GMT+{hour}"
        except ValueError:
            pass

    # If starts with timezone region, try to use as-is
    if "/" in timezone_input and (
        timezone_input.startswith(
            (
                "America/",
                "Europe/",
                "Asia/",
                "Africa/",
                "Pacific/",
                "Indian/",
                "Atlantic/",
            )
        )
    ):
        return timezone_input

    return None


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

    # Language to timezone suggestions mapping
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

    suggestions = language_timezone_map.get(language, [])

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
