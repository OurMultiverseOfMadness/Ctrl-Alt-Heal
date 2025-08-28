import uuid
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from pytz import UTC


class Prescription(BaseModel):  # type: ignore[misc]
    """Represents a single medication prescription."""

    name: str = Field(description="The name of the medication")
    dosage: str = Field(
        description="The dosage of the medication (e.g., '1 tablet', '10mg')"
    )
    frequency: str = Field(
        description="How often the medication should be taken (e.g., 'once a day', 'as needed')"
    )
    duration_days: int | None = Field(
        default=None,
        description="The duration in days for which the medication should be taken",
    )
    totalAmount: str = Field(
        description=("Total amount issued. For example, '10 tablets' or '200 ml'.")
    )
    additionalInstructions: str | None = Field(
        description=(
            "Other instructions from the doctor. For example, 'take after food'."
        ),
        default="",
    )
    extra_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="A catch-all for any extra fields returned by the AI",
    )


class Message(BaseModel):
    role: str
    content: str


class ConversationHistory(BaseModel):
    user_id: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    history: List[Message] = Field(default_factory=list)
    state: Dict[str, Any] = Field(default_factory=dict)
    last_updated: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class User(BaseModel):  # type: ignore[misc]
    """Represents a user of the application."""

    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    timezone: str | None = None
    language: str | None = None
    notes: str | None = None  # For storing long-term preferences and facts
    created_at: str
    updated_at: str


class Identity(BaseModel):
    pk: str | None = None  # provider#provider_user_id
    provider: str  # e.g., "telegram", "google"
    provider_user_id: str  # e.g., chat_id
    user_id: str  # The internal user_id
    created_at: str
