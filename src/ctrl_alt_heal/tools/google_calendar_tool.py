from typing import Any

from strands import tool

from ctrl_alt_heal.infrastructure.google_calendar_client import GoogleCalendarClient
from ctrl_alt_heal.infrastructure.users_store import UsersStore


@tool(
    description="Creates a new event in the user's Google Calendar.",
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "summary": {"type": "string"},
            "dtstart": {"type": "string", "format": "date-time"},
            "dtend": {"type": "string", "format": "date-time"},
        },
        "required": ["user_id", "summary", "dtstart", "dtend"],
    },
)
def create_google_calendar_event_tool(
    user_id: str, summary: str, dtstart: str, dtend: str
) -> dict[str, Any]:
    """A tool for creating a new event in the user's Google Calendar."""
    users_store = UsersStore()
    client = GoogleCalendarClient(user_id, users_store)
    return client.create_event(summary, dtstart, dtend)


@tool(
    description="Lists events from the user's Google Calendar.",
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "time_min": {"type": "string", "format": "date-time"},
            "time_max": {"type": "string", "format": "date-time"},
        },
        "required": ["user_id"],
    },
)
def list_google_calendar_events_tool(
    user_id: str, time_min: str | None = None, time_max: str | None = None
) -> dict[str, Any]:
    """A tool for listing events from the user's Google Calendar."""
    users_store = UsersStore()
    client = GoogleCalendarClient(user_id, users_store)
    return client.list_events(time_min, time_max)


@tool(
    description="Updates an event in the user's Google Calendar.",
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "event_id": {"type": "string"},
            "summary": {"type": "string"},
            "dtstart": {"type": "string", "format": "date-time"},
            "dtend": {"type": "string", "format": "date-time"},
        },
        "required": ["user_id", "event_id", "summary", "dtstart", "dtend"],
    },
)
def update_google_calendar_event_tool(
    user_id: str, event_id: str, summary: str, dtstart: str, dtend: str
) -> dict[str, Any]:
    """A tool for updating an event in the user's Google Calendar."""
    users_store = UsersStore()
    client = GoogleCalendarClient(user_id, users_store)
    return client.update_event(event_id, summary, dtstart, dtend)


@tool(
    description="Deletes an event from the user's Google Calendar.",
    inputSchema={
        "type": "object",
        "properties": {"user_id": {"type": "string"}, "event_id": {"type": "string"}},
        "required": ["user_id", "event_id"],
    },
)
def delete_google_calendar_event_tool(user_id: str, event_id: str) -> None:
    """A tool for deleting an event from the user's Google Calendar."""
    users_store = UsersStore()
    client = GoogleCalendarClient(user_id, users_store)
    client.delete_event(event_id)
