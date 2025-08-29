"""Timezone utilities for handling user timezone operations."""

from __future__ import annotations

import re
from typing import Optional

from ctrl_alt_heal.domain.models import User
from ctrl_alt_heal.utils.constants import TIMEZONE_MAPPINGS
from ctrl_alt_heal.utils.exceptions import TimezoneError


def normalize_timezone_input(timezone_input: str) -> Optional[str]:
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

    # Also check original case for exact matches
    if timezone_input in TIMEZONE_MAPPINGS:
        return TIMEZONE_MAPPINGS[timezone_input]

    # Handle UTC offset formats like "UTC+5", "GMT-8", "+0530"
    utc_pattern = r"^(utc|gmt)?\s*([+-]\d{1,2}):?(\d{2})?$"
    match = re.match(utc_pattern, normalized)
    if match:
        sign_hour = match.group(2)

        # Parse the offset
        try:
            sign = sign_hour[0]
            hour = int(sign_hour[1:])

            # Validate hour range
            if hour > 12:
                return None

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


def suggest_timezone_from_language(language: str) -> str:
    """
    Suggest a timezone based on language code.

    Args:
        language: Language code (e.g., "en-US", "zh-CN")

    Returns:
        Suggested timezone identifier
    """
    language_mappings = {
        # English variants
        "en-US": "America/New_York",
        "en-CA": "America/Toronto",
        "en-GB": "Europe/London",
        "en-AU": "Australia/Sydney",
        "en-NZ": "Pacific/Auckland",
        "en-IN": "Asia/Kolkata",
        "en-SG": "Asia/Singapore",
        "en-MY": "Asia/Kuala_Lumpur",
        "en-PH": "Asia/Manila",
        "en-HK": "Asia/Hong_Kong",
        # European languages
        "de-DE": "Europe/Berlin",
        "de-AT": "Europe/Vienna",
        "de-CH": "Europe/Zurich",
        "fr-FR": "Europe/Paris",
        "fr-CA": "America/Montreal",
        "es-ES": "Europe/Madrid",
        "es-MX": "America/Mexico_City",
        "es-AR": "America/Argentina/Buenos_Aires",
        "it-IT": "Europe/Rome",
        "pt-PT": "Europe/Lisbon",
        "pt-BR": "America/Sao_Paulo",
        "nl-NL": "Europe/Amsterdam",
        "sv-SE": "Europe/Stockholm",
        "no-NO": "Europe/Oslo",
        "da-DK": "Europe/Copenhagen",
        "fi-FI": "Europe/Helsinki",
        "pl-PL": "Europe/Warsaw",
        "ru-RU": "Europe/Moscow",
        "uk-UA": "Europe/Kiev",
        "tr-TR": "Europe/Istanbul",
        # Asian languages
        "zh-CN": "Asia/Shanghai",
        "zh-TW": "Asia/Taipei",
        "zh-HK": "Asia/Hong_Kong",
        "ja-JP": "Asia/Tokyo",
        "ko-KR": "Asia/Seoul",
        "th-TH": "Asia/Bangkok",
        "vi-VN": "Asia/Ho_Chi_Minh",
        "id-ID": "Asia/Jakarta",
        "ms-MY": "Asia/Kuala_Lumpur",
        "tl-PH": "Asia/Manila",
        # Middle Eastern languages
        "ar-SA": "Asia/Riyadh",
        "ar-AE": "Asia/Dubai",
        "ar-EG": "Africa/Cairo",
        "he-IL": "Asia/Jerusalem",
        "fa-IR": "Asia/Tehran",
        # Indian languages
        "hi-IN": "Asia/Kolkata",
        "bn-IN": "Asia/Kolkata",
        "ta-IN": "Asia/Kolkata",
        "te-IN": "Asia/Kolkata",
        "mr-IN": "Asia/Kolkata",
        "gu-IN": "Asia/Kolkata",
        "kn-IN": "Asia/Kolkata",
        "ml-IN": "Asia/Kolkata",
        "pa-IN": "Asia/Kolkata",
        # Other regions
        "af-ZA": "Africa/Johannesburg",
        "sw-KE": "Africa/Nairobi",
        "am-ET": "Africa/Addis_Ababa",
        "yo-NG": "Africa/Lagos",
        "zu-ZA": "Africa/Johannesburg",
    }

    return language_mappings.get(language, "UTC")


def validate_timezone(timezone_str: str) -> bool:
    """
    Validate if a timezone string is valid.

    Args:
        timezone_str: Timezone string to validate

    Returns:
        True if valid, False otherwise
    """
    if not timezone_str:
        return False

    try:
        import zoneinfo

        zoneinfo.ZoneInfo(timezone_str)
        return True
    except zoneinfo.ZoneInfoNotFoundError:
        return False


def get_user_timezone(user: User) -> Optional[str]:
    """
    Get the user's timezone, with fallback logic.

    Args:
        user: User object

    Returns:
        User's timezone or None if not set
    """
    if user.timezone:
        return user.timezone

    # Could implement fallback logic here based on user's language
    # For now, return None to prompt user for timezone
    return None


def get_friendly_timezone_name(timezone_str: str) -> str:
    """
    Get a user-friendly name for a timezone.

    Args:
        timezone_str: Timezone identifier

    Returns:
        User-friendly timezone name
    """
    friendly_names = {
        "America/New_York": "Eastern Time",
        "America/Chicago": "Central Time",
        "America/Denver": "Mountain Time",
        "America/Los_Angeles": "Pacific Time",
        "America/Anchorage": "Alaska Time",
        "Pacific/Honolulu": "Hawaii Time",
        "Europe/London": "London Time",
        "Europe/Paris": "Paris Time",
        "Europe/Berlin": "Berlin Time",
        "Asia/Tokyo": "Tokyo Time",
        "Asia/Shanghai": "Shanghai Time",
        "Asia/Singapore": "Singapore Time",
        "Asia/Kolkata": "India Time",
        "Australia/Sydney": "Sydney Time",
        "UTC": "UTC",
    }

    return friendly_names.get(timezone_str, timezone_str)


def normalize_timezone_input_with_exception(timezone_input: str) -> str:
    """
    Normalizes user timezone input to a standard timezone identifier with exception handling.

    Args:
        timezone_input: User's timezone input (e.g., "EST", "New York", "UTC+5")

    Returns:
        Standardized timezone identifier

    Raises:
        TimezoneError: If timezone is invalid or not recognized
    """
    if not timezone_input:
        raise TimezoneError("Timezone input cannot be empty", timezone_input)

    if not isinstance(timezone_input, str):
        raise TimezoneError("Timezone input must be a string", timezone_input)

    # Clean the input
    normalized = timezone_input.lower().strip()

    # Direct mapping lookup
    if normalized in TIMEZONE_MAPPINGS:
        return TIMEZONE_MAPPINGS[normalized]

    # Also check original case for exact matches
    if timezone_input in TIMEZONE_MAPPINGS:
        return TIMEZONE_MAPPINGS[timezone_input]

    # Handle UTC offset formats like "UTC+5", "GMT-8", "+0530"
    utc_pattern = r"^(utc|gmt)?\s*([+-]\d{1,2}):?(\d{2})?$"
    match = re.match(utc_pattern, normalized)
    if match:
        sign_hour = match.group(2)

        # Parse the offset
        try:
            sign = sign_hour[0]
            hour = int(sign_hour[1:])

            # Validate hour range
            if hour > 12:
                raise TimezoneError(
                    f"Invalid UTC offset: {timezone_input}", timezone_input
                )

            # Format as Etc/GMT offset (note: Etc/GMT uses inverted signs)
            if sign == "+":
                return f"Etc/GMT-{hour}"
            else:
                return f"Etc/GMT+{hour}"
        except ValueError:
            raise TimezoneError(
                f"Invalid UTC offset format: {timezone_input}", timezone_input
            )

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
        # Validate that it's a real timezone
        try:
            import zoneinfo

            zoneinfo.ZoneInfo(timezone_input)
            return timezone_input
        except zoneinfo.ZoneInfoNotFoundError:
            raise TimezoneError(
                f"Invalid timezone identifier: {timezone_input}", timezone_input
            )

    raise TimezoneError(f"Unrecognized timezone: {timezone_input}", timezone_input)


def validate_timezone_with_exception(timezone_str: str) -> None:
    """
    Validate if a timezone string is valid and raise exception if invalid.

    Args:
        timezone_str: Timezone string to validate

    Raises:
        TimezoneError: If timezone is invalid
    """
    if not timezone_str:
        raise TimezoneError("Timezone cannot be empty", timezone_str)

    if not isinstance(timezone_str, str):
        raise TimezoneError("Timezone must be a string", timezone_str)

    try:
        import zoneinfo

        zoneinfo.ZoneInfo(timezone_str)
    except zoneinfo.ZoneInfoNotFoundError:
        raise TimezoneError(f"Invalid timezone: {timezone_str}", timezone_str)
