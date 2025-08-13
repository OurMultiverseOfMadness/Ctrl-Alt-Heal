from pydantic import BaseModel, Field


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
