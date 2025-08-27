from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from ctrl_alt_heal.domain.models import Prescription
from ctrl_alt_heal.infrastructure.prescriptions_store import PrescriptionsStore


class ExtractionResult(BaseModel):  # type: ignore[misc]
    raw_json: dict[str, Any] | None = Field(
        description="Raw JSON output from the extractor"
    )
    confidence: float | None = Field(description="Confidence score from the extractor")
    prescriptions: list[Prescription] | None = Field(
        description="One or more extracted prescriptions"
    )


class ExtractionInput(BaseModel):  # type: ignore[misc]
    s3_bucket: str
    s3_key: str


class PrescriptionExtractor(Protocol):
    def extract(self, data: ExtractionInput) -> ExtractionResult: ...


def extract_prescription(
    extractor: PrescriptionExtractor,
    data: ExtractionInput,
    user_id: str,
) -> ExtractionResult:
    result = extractor.extract(data)
    # TODO: This is a simplistic mapping from raw JSON to structured data.
    # A more robust implementation would use a mapping layer and handle
    # variations in the extractor's output format.
    if result.raw_json:
        prescriptions = result.raw_json.get("prescriptions", [])
        result.prescriptions = [Prescription(**p) for p in prescriptions]
        for p in result.prescriptions:
            # TODO: This is a placeholder for a more robust implementation
            # that would handle chat_id and other context.
            PrescriptionsStore().save_prescription(
                user_id=user_id,
                name=p.name,
                dosage_text=p.dosage,
                frequency_text=p.frequency,
                status="active",
                source_bundle_sk=None,
                start_iso=None,
            )
    return result
