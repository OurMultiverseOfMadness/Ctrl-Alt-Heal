from __future__ import annotations

from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from ctrl_alt_heal.infrastructure.secrets_store import SecretsStore
from ctrl_alt_heal.infrastructure.users_store import UsersStore


class GoogleCalendarClient:
    def __init__(self, user_id: str, users_store: UsersStore) -> None:
        self.user_id = user_id
        self.users_store = users_store
        self.credentials = self._load_credentials()
        self.service = build("calendar", "v3", credentials=self.credentials)
        self.user = self.users_store.get_user(self.user_id)
        self.timezone = self.user.timezone if self.user else "UTC"

    def _load_credentials(self) -> Credentials:
        """Loads credentials from the secrets store."""
        secrets_store = SecretsStore()
        secret_name = f"google_calendar_credentials_{self.user_id}"
        secret_value = secrets_store.get_secret(secret_name)
        if not secret_value:
            raise Exception("No credentials found for this user.")
        return Credentials(**secret_value)

    def create_event(self, summary: str, dtstart: str, dtend: str) -> dict[str, Any]:
        """Creates a new event in the user's calendar."""
        event = {
            "summary": summary,
            "start": {"dateTime": dtstart, "timeZone": self.timezone},
            "end": {"dateTime": dtend, "timeZone": self.timezone},
        }
        return self.service.events().insert(calendarId="primary", body=event).execute()

    def list_events(
        self, time_min: str | None = None, time_max: str | None = None
    ) -> dict[str, Any]:
        """Lists events from the user's calendar."""
        return (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

    def update_event(
        self, event_id: str, summary: str, dtstart: str, dtend: str
    ) -> dict[str, Any]:
        """Updates an event in the user's calendar."""
        event = {
            "summary": summary,
            "start": {"dateTime": dtstart, "timeZone": self.timezone},
            "end": {"dateTime": dtend, "timeZone": self.timezone},
        }
        return (
            self.service.events()
            .update(calendarId="primary", eventId=event_id, body=event)
            .execute()
        )

    def delete_event(self, event_id: str) -> None:
        """Deletes an event from the user's calendar."""
        self.service.events().delete(calendarId="primary", eventId=event_id).execute()
