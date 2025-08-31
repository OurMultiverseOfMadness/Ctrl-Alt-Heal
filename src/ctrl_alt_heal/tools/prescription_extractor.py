from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from ctrl_alt_heal.domain.models import Prescription
from ctrl_alt_heal.infrastructure.prescriptions_store import PrescriptionsStore
from ctrl_alt_heal.infrastructure.fhir_store import FhirStore
import uuid
from datetime import datetime, UTC


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
    # The result from the extractor now contains parsed Prescription objects.
    # We can use them directly to save to the database.
    if result.prescriptions:
        prescriptions_store = PrescriptionsStore()
        fhir_store = FhirStore()

        for p in result.prescriptions:
            # Save to the primary prescriptions table first
            prescription_sk = prescriptions_store.save_prescription(
                user_id=user_id,
                name=p.name,
                dosage_text=p.dosage,
                frequency_text=p.frequency,
                status="active",
                source_bundle_sk=None,  # We'll link this after saving the FHIR bundle
                start_iso=None,
            )

            # Construct and save a corresponding FHIR bundle
            fhir_bundle = _create_fhir_bundle(p, user_id)
            bundle_sk = fhir_store.save_bundle(user_id=user_id, bundle=fhir_bundle)

            # Link the prescription to the FHIR bundle by updating the sourceBundleSK
            prescriptions_store.update_prescription_source_bundle(
                user_id=user_id,
                prescription_id=prescription_sk,
                source_bundle_sk=bundle_sk,
            )

    return result


def _create_fhir_bundle(prescription: Prescription, user_id: str) -> dict[str, Any]:
    """Creates a FHIR Bundle with a MedicationRequest resource."""
    medication_request_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "meta": {"lastUpdated": now},
        "type": "transaction",
        "entry": [
            {
                "fullUrl": f"urn:uuid:{medication_request_id}",
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": medication_request_id,
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {"text": prescription.name},
                    "subject": {"reference": f"Patient/{user_id}"},
                    "authoredOn": now,
                    "dosageInstruction": [
                        {
                            "text": f"{prescription.dosage}, {prescription.frequency}",
                            "timing": {
                                "repeat": {
                                    "frequency": 1,
                                    "period": 1,
                                    "periodUnit": "d",
                                }
                            },  # Placeholder
                        }
                    ],
                },
                "request": {"method": "POST", "url": "MedicationRequest"},
            }
        ],
    }
