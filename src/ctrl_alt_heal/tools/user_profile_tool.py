from __future__ import annotations

from typing import Any

from strands import tool

from ctrl_alt_heal.infrastructure.users_store import UsersStore


@tool(
    description="Updates a user's profile information, such as timezone or language.",
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
    description="Retrieves a user's profile information.",
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

    return {"status": "success", "profile": user.model_dump()}
