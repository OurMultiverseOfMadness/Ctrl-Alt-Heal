from typing import Any

from strands import tool

from ctrl_alt_heal.infrastructure.google_calendar_client import GoogleCalendarClient
from ctrl_alt_heal.infrastructure.users_store import UsersStore


@tool(
    name="create_google_calendar_event",
    description=(
        "Creates a new appointment or event in the user's Google Calendar. "
        "Example Triggers: 'Schedule a doctor's appointment for Tuesday at 2pm', 'Remind me to pick up my prescription tomorrow.'"
    ),
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
    name="list_google_calendar_events",
    description=(
        "Lists upcoming appointments and events from the user's Google Calendar. "
        "Use this to answer questions about their schedule. "
        "Example Triggers: 'What appointments do I have this week?', 'When is my next doctor's visit?'"
    ),
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
    name="update_google_calendar_event",
    description=(
        "Updates an existing appointment or event in the user's Google Calendar. "
        "You MUST have the event_id to update an event. "
        "Example Triggers: 'Reschedule my Tuesday appointment to Wednesday', 'My appointment time has changed.'"
    ),
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
    name="delete_google_calendar_event",
    description=(
        "Deletes an existing appointment or event from the user's Google Calendar. "
        "You MUST have the event_id to delete an event. "
        "Example Triggers: 'Cancel my appointment on Tuesday', 'I don't need that reminder anymore.'"
    ),
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
