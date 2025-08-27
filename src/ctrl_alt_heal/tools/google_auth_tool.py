from __future__ import annotations

import secrets

from google_auth_oauthlib.flow import Flow
from strands import tool

from ctrl_alt_heal.config import settings
from ctrl_alt_heal.infrastructure.history_store import HistoryStore
from ctrl_alt_heal.infrastructure.secrets_store import SecretsStore

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


@tool(
    description="Generates a Google Calendar authentication URL.",
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
        },
        "required": ["user_id"],
    },
)
def generate_auth_url_tool(user_id: str) -> str:
    """A tool for generating a Google Calendar authentication URL."""
    flow = Flow.from_client_secrets_file(
        settings.google_client_secrets_file,
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )
    state = secrets.token_urlsafe(16)
    authorization_url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", state=state
    )

    history_store = HistoryStore()
    conversation_history = history_store.get_history(user_id)
    conversation_history.state["oauth_state"] = state
    history_store.save_history(conversation_history)

    return authorization_url


@tool(
    description="Exchanges an authorization code for a refresh token.",
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "code": {"type": "string"},
            "state": {"type": "string"},
        },
        "required": ["user_id", "code", "state"],
    },
)
def exchange_code_for_token_tool(user_id: str, code: str, state: str) -> str:
    """A tool for exchanging an authorization code for a refresh token."""
    history_store = HistoryStore()
    conversation_history = history_store.get_history(user_id)
    saved_state = conversation_history.state.pop("oauth_state", None)
    history_store.save_history(conversation_history)

    if not saved_state or saved_state != state:
        return "Error: Invalid state. Please try again."

    flow = Flow.from_client_secrets_file(
        settings.google_client_secrets_file,
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials

    secrets_store = SecretsStore()
    secret_name = f"google_calendar_credentials_{user_id}"
    secret_value = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
    secrets_store.save_secret(secret_name, secret_value)

    return "Successfully authenticated!"
