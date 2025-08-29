from __future__ import annotations

from typing import Any

from strands import tool

from ctrl_alt_heal.infrastructure.users_store import UsersStore


@tool(
    name="update_user_profile",
    description=(
        "Updates a user's profile with non-medical information. "
        "This is for saving user preferences like timezone or preferred language. "
        "Example Triggers: 'My timezone is EST', 'Please speak to me in Spanish.'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "timezone": {"type": "string"},
            "language": {"type": "string"},
        },
        "required": ["user_id"],
    },
)
def update_user_profile_tool(
    user_id: str, timezone: str | None = None, language: str | None = None
) -> dict[str, Any]:
    """A tool for updating a user's profile."""
    users_store = UsersStore()
    user = users_store.get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found."}

    if timezone:
        user.timezone = timezone
    if language:
        user.language = language

    users_store.upsert_user(user)
    return {"status": "success", "message": "User profile updated."}


@tool(
    name="get_user_profile",
    description=(
        "Retrieves the user's complete profile, including stored prescriptions, appointments, "
        "and personal details like timezone. This should be your FIRST step for almost any "
        "question about the user's existing data. "
        "Example Triggers: 'What are my prescriptions?', 'Do I have any appointments?', 'What timezone do you have for me?'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
        },
        "required": ["user_id"],
    },
)
def get_user_profile_tool(user_id: str) -> dict[str, Any]:
    """A tool for retrieving a user's profile."""
    users_store = UsersStore()
    user = users_store.get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found."}

    # Debug logging to see user profile data
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"User profile data: {user.model_dump()}")
    logger.info(f"User timezone: {user.timezone}")
    logger.info(f"User language: {user.language}")

    return {"status": "success", "profile": user.model_dump()}


@tool(
    name="save_user_notes",
    description=(
        "Saves or updates long-term notes and preferences about a user. "
        "Use this to remember key facts like allergies, primary doctor, or communication style. "
        "The notes should be a concise summary of all important facts. When updating, provide the full, complete set of notes. "
        "Example Triggers: The user says 'My doctor is Dr. Smith', or 'Please remember I'm allergic to penicillin'."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "notes": {"type": "string"},
        },
        "required": ["user_id", "notes"],
    },
)
def save_user_notes_tool(user_id: str, notes: str) -> dict[str, Any]:
    """A tool for saving long-term user notes and preferences."""
    users_store = UsersStore()
    user = users_store.get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found."}

    user.notes = notes
    users_store.upsert_user(user)
    return {"status": "success", "message": "User notes saved."}
