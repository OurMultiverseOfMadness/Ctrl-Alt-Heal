from __future__ import annotations

from typing import Any

from ....config.settings import Settings
from ....contexts.prescriptions.application.use_cases.extract_prescription import (
    ExtractionInput,
)
from ....contexts.prescriptions.infrastructure.ai.bedrock_extractor import (
    BedrockExtractor,
)
from ....interface.telegram.download import download_and_store_telegram_file
from ....shared.infrastructure.logger import get_logger


def ingest_prescription_multi_tool(payload: dict[str, Any]) -> dict[str, Any]:
    logger = get_logger(__name__)
    settings = Settings.load()
    update = payload.get("update")
    if not isinstance(update, dict):
        logger.warning(
            "tool_outcome",
            extra={"tool": "ingest_prescription_multi", "status": "missing_update"},
        )
        return {"error": "missing_update"}

    try:
        loc = download_and_store_telegram_file(update, settings)
        extractor = BedrockExtractor(
            model_id=settings.bedrock_extract_model_id or settings.bedrock_model_id,
            region_name=settings.bedrock_region or settings.aws_region,
        )
        result = extractor.extract(
            ExtractionInput(s3_bucket=loc.s3_bucket, s3_key=loc.s3_key)
        )

        # Normalize to list of medication dicts
        items: list[dict[str, object]] = []
        raw = result.raw_json
        if isinstance(raw, dict):
            meds = raw.get("medications")
            if isinstance(meds, list):
                for m in meds:
                    if isinstance(m, dict):
                        items.append(m)
        elif isinstance(raw, list):
            for m in raw:
                if isinstance(m, dict):
                    items.append(m)

        logger.info("tool_outcome")
        return {
            "status": "ok",
            "s3_bucket": loc.s3_bucket,
            "s3_key": loc.s3_key,
            "items": items,
        }
    except Exception:  # pragma: no cover
        logger.exception("tool_outcome")
        return {"error": "ingest_multi_failed"}
