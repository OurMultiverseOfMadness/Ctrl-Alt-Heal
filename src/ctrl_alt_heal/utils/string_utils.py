"""String utilities for common string manipulation operations."""

from __future__ import annotations

import re
from typing import List


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string for use as a filename.

    Args:
        name: Original string

    Returns:
        Sanitized filename
    """
    if not name:
        return "unnamed"

    # Replace spaces with underscores
    sanitized = name.replace(" ", "_")

    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", sanitized)

    # Remove multiple consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")

    return sanitized or "unnamed"


def normalize_timezone_string(time_str: str) -> str:
    """
    Normalize timezone string format.

    Args:
        time_str: Time string to normalize

    Returns:
        Normalized time string
    """
    if not time_str:
        return time_str

    # Replace Z with +00:00 for consistency
    return time_str.replace("Z", "+00:00")


def clean_message_text(text: str) -> str:
    """
    Clean message text by removing extra whitespace and normalizing.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    cleaned = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()

    return cleaned


def clean_xml_tags(text: str) -> str:
    """
    Remove XML tags from text.

    Args:
        text: Text containing XML tags

    Returns:
        Text with XML tags removed
    """
    if not text:
        return ""

    # Remove XML tags
    cleaned = re.sub(r"<[^>]+>", "", text)

    # Clean up extra whitespace and normalize spacing
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip()

    return cleaned


def split_message_for_telegram(text: str, max_length: int = 4096) -> List[str]:
    """
    Split a long message into chunks suitable for Telegram.
    Now uses the robust MessageSplitter internally.

    Args:
        text: Text to split
        max_length: Maximum length per chunk

    Returns:
        List of message chunks
    """
    if not text:
        return []

    from ctrl_alt_heal.utils.telegram_formatter import MessageSplitter

    splitter = MessageSplitter(max_length)
    return splitter.split_message(text, preserve_formatting=False)


def normalize_medication_name(name: str) -> str:
    """
    Normalize medication name for comparison.

    Args:
        name: Medication name

    Returns:
        Normalized name
    """
    if not name:
        return ""

    # Convert to lowercase and remove extra whitespace
    normalized = name.lower().strip()

    # Remove common prefixes/suffixes that don't affect matching
    normalized = re.sub(r"\b(tab|tablet|cap|capsule|mg|mcg|ml)\b", "", normalized)

    # Remove extra whitespace
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized.strip()


def extract_medication_name_from_filename(filename: str) -> str:
    """
    Extract medication name from filename.

    Args:
        filename: Filename containing medication name

    Returns:
        Extracted medication name
    """
    if not filename:
        return ""

    # Remove file extension
    name = filename.rsplit(".", 1)[0]

    # Remove timestamp and common suffixes
    name = re.sub(r"_\d{8}_\d{6}$", "", name)  # Remove timestamp
    name = re.sub(r"_(reminders|schedule|auto_schedule)$", "", name)  # Remove suffixes

    # Replace underscores with spaces
    name = name.replace("_", " ")

    return name.strip()
