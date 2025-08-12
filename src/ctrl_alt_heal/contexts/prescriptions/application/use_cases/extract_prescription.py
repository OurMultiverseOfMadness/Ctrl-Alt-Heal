from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ExtractionInput:
    s3_bucket: str
    s3_key: str


@dataclass(frozen=True)
class ExtractionResult:
    raw_json: dict[str, Any]
    confidence: float


class PrescriptionExtractor(Protocol):
    def extract(
        self, data: ExtractionInput
    ) -> ExtractionResult:  # pragma: no cover - interface
        ...


def extract_prescription(
    extractor: PrescriptionExtractor, data: ExtractionInput
) -> ExtractionResult:
    result = extractor.extract(data)
    # Minimal validation
    if not isinstance(result.raw_json, dict):
        raise ValueError("Invalid extraction result")
    if not (0.0 <= result.confidence <= 1.0):
        raise ValueError("Invalid confidence")
    return result
