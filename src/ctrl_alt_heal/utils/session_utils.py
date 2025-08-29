"""Session utilities for managing user sessions and conversation history."""

from __future__ import annotations

from datetime import datetime, UTC, timedelta
from typing import Optional, Tuple

from ctrl_alt_heal.domain.models import ConversationHistory
from ctrl_alt_heal.utils.constants import SESSION_TIMEOUT_MINUTES
from ctrl_alt_heal.utils.history_management import (
    should_create_new_session_due_to_history_size,
    cleanup_history_state,
)


def is_session_expired(
    last_updated: str, timeout_minutes: int = SESSION_TIMEOUT_MINUTES
) -> bool:
    """
    Check if a session has expired based on inactivity (last update time).

    Args:
        last_updated: ISO format timestamp of last update
        timeout_minutes: Session timeout in minutes (default: 15 minutes of inactivity)

    Returns:
        True if session has expired due to inactivity
    """
    try:
        last_updated_dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        timeout_threshold = datetime.now(UTC) - timedelta(minutes=timeout_minutes)
        return last_updated_dt < timeout_threshold
    except (ValueError, AttributeError):
        # If we can't parse the timestamp, consider it expired
        return True


def get_session_inactivity_minutes(last_updated: str) -> int:
    """
    Get the number of minutes since the session was last active.

    Args:
        last_updated: ISO format timestamp of last update

    Returns:
        Minutes of inactivity
    """
    try:
        last_updated_dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        now = datetime.now(UTC)
        return int((now - last_updated_dt).total_seconds() / 60)
    except (ValueError, AttributeError):
        # If we can't parse the timestamp, return a large number
        return 999999


def should_create_new_session(
    history: Optional[ConversationHistory],
    timeout_minutes: int = SESSION_TIMEOUT_MINUTES,
) -> Tuple[bool, str]:
    """
    Determine if a new session should be created based on inactivity or history size.

    Args:
        history: Existing conversation history (can be None)
        timeout_minutes: Session timeout in minutes

    Returns:
        Tuple of (should_create_new, reason)
    """
    if not history:
        return True, "No existing session found"

    # Check for session expiration due to inactivity
    if is_session_expired(history.last_updated, timeout_minutes):
        inactivity_minutes = get_session_inactivity_minutes(history.last_updated)
        return (
            True,
            f"Session expired due to {inactivity_minutes} minutes of inactivity",
        )

    # Check for session expiration due to history size
    should_create_size, size_reason = should_create_new_session_due_to_history_size(
        history
    )
    if should_create_size:
        return True, size_reason

    return False, "Session is still active"


def create_new_session(user_id: str) -> ConversationHistory:
    """
    Create a new conversation session for a user.

    Args:
        user_id: User identifier

    Returns:
        New conversation history object
    """
    now = datetime.now(UTC).isoformat()
    return ConversationHistory(user_id=user_id, history=[], last_updated=now)


def update_session_timestamp(history: ConversationHistory) -> ConversationHistory:
    """
    Update the last updated timestamp of a session to keep it active.
    Also clean up history state to prevent bloat.

    Args:
        history: Conversation history object

    Returns:
        Updated conversation history object
    """
    history.last_updated = datetime.now(UTC).isoformat()
    # Clean up history state to prevent bloat
    history = cleanup_history_state(history)
    return history


def add_message_to_session(
    history: ConversationHistory, role: str, content: str
) -> ConversationHistory:
    """
    Add a message to the conversation session and update the timestamp.

    Args:
        history: Conversation history object
        role: Message role (user/assistant)
        content: Message content

    Returns:
        Updated conversation history object
    """
    from ctrl_alt_heal.domain.models import Message

    message = Message(role=role, content=content)
    history.history.append(message)
    history.last_updated = datetime.now(UTC).isoformat()

    return history


def get_session_duration_minutes(history: ConversationHistory) -> int:
    """
    Get the duration of a session in minutes.

    Args:
        history: Conversation history object

    Returns:
        Session duration in minutes
    """
    try:
        if not history.history:
            return 0
        # Use the session's last_updated as the end time
        # For start time, we'll estimate based on when the first message was likely added
        # Since Message doesn't have timestamp, we'll use a reasonable estimate
        end_time = datetime.fromisoformat(history.last_updated.replace("Z", "+00:00"))

        # Estimate start time as 1 minute before the first message was added
        # This is a reasonable approximation since we don't store individual message timestamps
        estimated_start_time = end_time - timedelta(minutes=len(history.history))

        return int((end_time - estimated_start_time).total_seconds() / 60)
    except (ValueError, AttributeError):
        return 0


def get_session_message_count(history: ConversationHistory) -> int:
    """
    Get the number of messages in a session.

    Args:
        history: Conversation history object

    Returns:
        Number of messages
    """
    return len(history.history)


def clear_session_history(history: ConversationHistory) -> ConversationHistory:
    """
    Clear the message history while keeping the session active.

    Args:
        history: Conversation history object

    Returns:
        Updated conversation history object
    """
    history.history = []
    history.last_updated = datetime.now(UTC).isoformat()
    return history


def is_session_active(
    history: ConversationHistory, timeout_minutes: int = SESSION_TIMEOUT_MINUTES
) -> bool:
    """
    Check if a session is currently active based on inactivity timeout.

    Args:
        history: Conversation history object
        timeout_minutes: Session timeout in minutes (default: 15 minutes of inactivity)

    Returns:
        True if session is active (not expired due to inactivity)
    """
    return not is_session_expired(history.last_updated, timeout_minutes)


def get_session_summary(history: ConversationHistory) -> dict:
    """
    Get a comprehensive summary of the session.

    Args:
        history: Conversation history object

    Returns:
        Session summary dictionary
    """
    inactivity_minutes = get_session_inactivity_minutes(history.last_updated)

    return {
        "user_id": history.user_id,
        "message_count": get_session_message_count(history),
        "duration_minutes": get_session_duration_minutes(history),
        "inactivity_minutes": inactivity_minutes,
        "last_updated": history.last_updated,
        "is_active": is_session_active(history),
        "timeout_minutes": SESSION_TIMEOUT_MINUTES,
        "will_expire_in_minutes": max(0, SESSION_TIMEOUT_MINUTES - inactivity_minutes),
    }


def extend_session(
    history: ConversationHistory, additional_minutes: int = SESSION_TIMEOUT_MINUTES
) -> ConversationHistory:
    """
    Extend the session timeout by updating the last_updated timestamp.

    Args:
        history: Conversation history object
        additional_minutes: Additional minutes to extend the session

    Returns:
        Updated conversation history object
    """
    # Update the timestamp to extend the session
    history.last_updated = datetime.now(UTC).isoformat()
    return history


def get_session_status(history: Optional[ConversationHistory]) -> dict:
    """
    Get the current status of a session.

    Args:
        history: Conversation history object (can be None)

    Returns:
        Session status dictionary
    """
    if not history:
        return {"exists": False, "is_active": False, "reason": "No session exists"}

    is_active = is_session_active(history)
    inactivity_minutes = get_session_inactivity_minutes(history.last_updated)

    return {
        "exists": True,
        "is_active": is_active,
        "inactivity_minutes": inactivity_minutes,
        "timeout_minutes": SESSION_TIMEOUT_MINUTES,
        "will_expire_in_minutes": max(0, SESSION_TIMEOUT_MINUTES - inactivity_minutes),
        "reason": "Session active"
        if is_active
        else f"Session expired ({inactivity_minutes} minutes of inactivity)",
    }
