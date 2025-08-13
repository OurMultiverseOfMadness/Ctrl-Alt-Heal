from dataclasses import dataclass
from typing import Any, Protocol

from src.ctrl_alt_heal.contexts.prescriptions.domain.prescription import Prescription


@dataclass
class ExtractionInput:
    s3_bucket: str
    s3_key: str


@dataclass
class ExtractionResult:
    raw_json: dict[str, Any]
    confidence: float = 0.0


class PrescriptionExtractor(Protocol):
    def extract(self, data: ExtractionInput) -> ExtractionResult:  # pragma: no cover
        ...


def extract_prescription(
    extractor: PrescriptionExtractor, data: ExtractionInput
) -> ExtractionResult:
    """Run the configured extractor against the provided S3 object."""
    return extractor.extract(data)


def extract_prescriptions_list(summary: str) -> list[Prescription] | None:
    """
    Placeholder multi-extraction from a text summary.
    For MVP, return an empty list and let the chat layer summarise for the user.
    """
    _ = summary
    return []


def to_fhir_bundle(
    chat_id: int, extraction: dict[str, Any] | list[dict[str, Any]]
) -> dict[str, Any]:
    """Minimal FHIR bundle containing MedicationStatement entries.

    This is a simplified placeholder suitable for storage and later expansion.
    """
    meds: list[dict[str, Any]] = []
    if isinstance(extraction, dict):
        maybe = extraction.get("medications")
        if isinstance(maybe, list):
            for m in maybe:
                if isinstance(m, dict):
                    meds.append(m)
    elif isinstance(extraction, list):
        for m in extraction:
            if isinstance(m, dict):
                meds.append(m)

    entries: list[dict[str, Any]] = []
    for m in meds:
        name = m.get("name") or m.get("medication") or m.get("drug") or "unknown"
        dosage = m.get("dosage") or m.get("dose") or ""
        frequency = m.get("frequency")
        if isinstance(frequency, dict):
            frequency = frequency.get("free_text") or frequency.get("text") or ""
        stmt = {
            "resourceType": "MedicationStatement",
            "status": "active",
            "medicationCodeableConcept": {"text": name},
            "dosage": [{"text": f"{dosage}, {frequency}".strip(", ")}],
            "subject": {"reference": f"Patient/CHAT-{chat_id}"},
        }
        entries.append({"resource": stmt})

    bundle = {"resourceType": "Bundle", "type": "collection", "entry": entries}
    return bundle
