from __future__ import annotations

from typing import Any
from datetime import UTC, datetime

from strands import tool

from ctrl_alt_heal.infrastructure.identities_store import IdentitiesStore
from ctrl_alt_heal.infrastructure.users_store import UsersStore
from ctrl_alt_heal.domain.models import Identity, User


@tool(
    name="find_user_by_identity",
    description=(
        "Finds a user by their identity provider information (e.g., Telegram chat ID). "
        "Use this when you need to check if a user already exists in the system. "
        "Example: When a user interacts but you're not sure if they're registered."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "provider": {
                "type": "string",
                "description": "The identity provider (e.g., 'telegram', 'email')",
            },
            "provider_user_id": {
                "type": "string",
                "description": "The user ID from the provider (e.g., Telegram chat ID)",
            },
        },
        "required": ["provider", "provider_user_id"],
    },
)
def find_user_by_identity_tool(provider: str, provider_user_id: str) -> dict[str, Any]:
    """Finds a user by their identity provider information."""
    identities_store = IdentitiesStore()
    users_store = UsersStore()

    # Look up user ID by identity
    user_id = identities_store.find_user_id_by_identity(provider, provider_user_id)

    if not user_id:
        return {
            "status": "not_found",
            "message": f"No user found for {provider} ID: {provider_user_id}",
        }

    # Get the user details
    user = users_store.get_user(user_id)
    if not user:
        return {
            "status": "error",
            "message": f"User ID {user_id} exists in identity table but not in users table",
        }

    return {
        "status": "found",
        "user": user.model_dump(),
        "user_id": user_id,
    }


@tool(
    name="create_user_with_identity",
    description=(
        "Creates a new user and links their identity provider information. "
        "Use this when a new user interacts with the system for the first time. "
        "Example: When someone starts a conversation on Telegram and doesn't exist yet."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "provider": {
                "type": "string",
                "description": "The identity provider (e.g., 'telegram', 'email')",
            },
            "provider_user_id": {
                "type": "string",
                "description": "The user ID from the provider (e.g., Telegram chat ID)",
            },
            "first_name": {
                "type": "string",
                "description": "User's first name (optional)",
            },
            "last_name": {
                "type": "string",
                "description": "User's last name (optional)",
            },
            "username": {
                "type": "string",
                "description": "User's username (optional)",
            },
        },
        "required": ["provider", "provider_user_id"],
    },
)
def create_user_with_identity_tool(
    provider: str,
    provider_user_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    username: str | None = None,
) -> dict[str, Any]:
    """Creates a new user and links their identity provider information."""
    identities_store = IdentitiesStore()
    users_store = UsersStore()

    # Check if user already exists
    existing_user_id = identities_store.find_user_id_by_identity(
        provider, provider_user_id
    )
    if existing_user_id:
        return {
            "status": "already_exists",
            "message": f"User already exists for {provider} ID: {provider_user_id}",
            "user_id": existing_user_id,
        }

    # Create new user
    now = datetime.now(UTC).isoformat()
    user = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        created_at=now,
        updated_at=now,
    )

    # Save user to get user_id
    users_store.upsert_user(user)
    user_id = user.user_id

    # Create and link identity
    identity = Identity(
        pk=f"{provider}#{provider_user_id}",
        provider=provider,
        provider_user_id=provider_user_id,
        user_id=user_id,
        created_at=now,
    )
    identities_store.link_identity(identity)

    return {
        "status": "created",
        "message": f"Created new user and linked {provider} identity",
        "user_id": user_id,
        "user": user.model_dump(),
    }


@tool(
    name="get_or_create_user",
    description=(
        "Gets an existing user or creates a new one if they don't exist. "
        "This is a convenience tool that combines find_user_by_identity and create_user_with_identity. "
        "Use this as your first step when a user interacts with the system."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "provider": {
                "type": "string",
                "description": "The identity provider (e.g., 'telegram', 'email')",
            },
            "provider_user_id": {
                "type": "string",
                "description": "The user ID from the provider (e.g., Telegram chat ID)",
            },
            "first_name": {
                "type": "string",
                "description": "User's first name (used if creating new user)",
            },
            "last_name": {
                "type": "string",
                "description": "User's last name (used if creating new user)",
            },
            "username": {
                "type": "string",
                "description": "User's username (used if creating new user)",
            },
        },
        "required": ["provider", "provider_user_id"],
    },
)
def get_or_create_user_tool(
    provider: str,
    provider_user_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    username: str | None = None,
) -> dict[str, Any]:
    """Gets an existing user or creates a new one if they don't exist."""
    # First try to find existing user
    find_result = find_user_by_identity_tool(provider, provider_user_id)

    if find_result["status"] == "found":
        return {
            "status": "existing_user",
            "message": "Found existing user",
            "user_id": find_result["user_id"],
            "user": find_result["user"],
        }

    # User not found, create new one
    create_result = create_user_with_identity_tool(
        provider, provider_user_id, first_name, last_name, username
    )

    if create_result["status"] == "created":
        return {
            "status": "new_user",
            "message": "Created new user",
            "user_id": create_result["user_id"],
            "user": create_result["user"],
        }

    # Something went wrong
    return {
        "status": "error",
        "message": f"Failed to get or create user: {create_result.get('message', 'Unknown error')}",
    }
