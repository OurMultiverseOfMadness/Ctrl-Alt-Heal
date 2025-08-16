from dataclasses import dataclass
from typing import Any, Protocol

from src.ctrl_alt_heal.contexts.prescriptions.domain.prescription import Prescription
from src.ctrl_alt_heal.shared.infrastructure.prescriptions_store import (
    save_prescription,
)


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


def materialize_prescriptions_from_bundle(
    chat_id: int, bundle: dict[str, Any], source_bundle_sk: str | None = None
) -> None:
    entries = bundle.get("entry") if isinstance(bundle, dict) else None
    if not isinstance(entries, list):
        return
    for entry in entries:
        res = entry.get("resource") if isinstance(entry, dict) else None
        if not isinstance(res, dict):
            continue
        if res.get("resourceType") not in {"MedicationRequest", "MedicationStatement"}:
            continue
        name = ((res.get("medicationCodeableConcept") or {}).get("text")) or ""
        di = res.get("dosageInstruction")
        dosage_text = None
        if isinstance(di, list) and di:
            first = di[0]
            if isinstance(first, dict):
                dosage_text = first.get("text")
        status = (
            (res.get("status") or "active")
            if isinstance(res.get("status"), str)
            else "active"
        )
        authored_on = (
            res.get("authoredOn") if isinstance(res.get("authoredOn"), str) else None
        )
        save_prescription(
            chat_id=chat_id,
            name=str(name),
            dosage_text=str(dosage_text) if isinstance(dosage_text, str) else None,
            frequency_text=None,
            status=str(status),
            source_bundle_sk=source_bundle_sk,
            start_iso=authored_on,
            extra={},
        )
