import uuid
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class Prescription(BaseModel):  # type: ignore[misc]
    name: str = Field(description="Name of the drug/medicine")
    dosage: str = Field(
        description=(
            "Amount to take each time, in drug units. For example, '1 tablet' or "
            "'5 ml'."
        )
    )
    frequency: str = Field(
        description=(
            "How often to take the drug. For example, 'once daily' or '3 times daily'."
        )
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


class Message(BaseModel):
    role: str
    content: str


class ConversationHistory(BaseModel):
    user_id: str
    history: List[Message] = Field(default_factory=list)
    state: Dict[str, Any] = Field(default_factory=dict)


class User(BaseModel):
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
    provider: str  # e.g., "telegram", "google"
    provider_user_id: str  # e.g., chat_id
    user_id: str  # The internal user_id
    created_at: str
