from __future__ import annotations

from typing import Any

from ....config.settings import Settings
from ....contexts.prescriptions.application.use_cases.extract_prescription import (
    ExtractionInput,
    extract_prescription,
)
from ....contexts.prescriptions.infrastructure.ai.bedrock_extractor import (
    BedrockExtractor,
)
from ....interface.telegram.download import download_and_store_telegram_file
from ....shared.infrastructure.logger import get_logger


def ingest_prescription_file_tool(payload: dict[str, Any]) -> dict[str, Any]:
    logger = get_logger(__name__)
    settings = Settings.load()
    update = payload.get("update")
    if not isinstance(update, dict):
        logger.warning(
            "tool_outcome",
            extra={"tool": "ingest_prescription_file", "status": "missing_update"},
        )
        return {"error": "missing_update"}
    try:
        loc = download_and_store_telegram_file(update, settings)
        extractor = BedrockExtractor(
            model_id=settings.bedrock_extract_model_id or settings.bedrock_model_id,
            region_name=settings.bedrock_region or settings.aws_region,
        )
        result = extract_prescription(
            extractor, ExtractionInput(s3_bucket=loc.s3_bucket, s3_key=loc.s3_key)
        )
        logger.info(
            "tool_outcome",
            extra={
                "tool": "ingest_prescription_file",
                "status": "ok",
                "s3_key": loc.s3_key,
                "confidence": result.confidence,
            },
        )
        return {
            "status": "ok",
            "s3_bucket": loc.s3_bucket,
            "s3_key": loc.s3_key,
            "confidence": result.confidence,
            "extraction": result.raw_json,
        }
    except Exception as exc:  # pragma: no cover
        logger.exception(
            "tool_outcome",
            extra={
                "tool": "ingest_prescription_file",
                "status": "error",
                "error": str(exc),
            },
        )
        return {"error": "ingest_failed"}
