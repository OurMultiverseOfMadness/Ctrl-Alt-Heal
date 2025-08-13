from typing import Optional
from pydantic import BaseModel, Field


class Prescription(BaseModel):
    name: str = Field(description="Name of the drug/medicine")
    dosage: str = Field(
        description="Amount of drug to take each time, in the units of the drug prescibed. For example, '1 tablet' or '5ml'."
    )
    frequency: str = Field(
        description="How often to take the drug. For example, '1 time a day' or '3 times daily'."
    )
    totalAmount: str = Field(
        description="Total amount of the drug issued to the patient. For example, '10 tablets' or '200 ml'."
    )
    additionalInstructions: Optional[str] = Field(
        description="Any other instructions while taking the medicine given by the doctor. For example, 'take after food'.",
        default="",
    )
