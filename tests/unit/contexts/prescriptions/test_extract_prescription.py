from __future__ import annotations

from dataclasses import dataclass

from src.ctrl_alt_heal.contexts.prescriptions.application.use_cases import (
    extract_prescription as ep,
)


@dataclass
class FakeExtractor(ep.PrescriptionExtractor):
    def extract(self, data: ep.ExtractionInput) -> ep.ExtractionResult:  # type: ignore[override]
        return ep.ExtractionResult(raw_json={"ok": True}, confidence=0.9)


def test_extract_prescription_happy_path() -> None:
    extractor = FakeExtractor()  # type: ignore[abstract]
    result = ep.extract_prescription(
        extractor, ep.ExtractionInput(s3_bucket="b", s3_key="k")
    )
    assert result.raw_json["ok"] is True
    assert 0.0 <= result.confidence <= 1.0
