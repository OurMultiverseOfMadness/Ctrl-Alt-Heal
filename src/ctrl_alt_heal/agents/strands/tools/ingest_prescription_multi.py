from __future__ import annotations

from typing import Any

from ....config.settings import Settings
from ....contexts.prescriptions.application.use_cases.extract_prescription import (
    extract_prescriptions_list,
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
        # For MVP: rely on upstream summary (not present here); return only S3 info.
        # Later: run a VLM summary then pass to extract_prescriptions_list.
        result_list = extract_prescriptions_list(
            summary=f"s3://{loc.s3_bucket}/{loc.s3_key}"
        )
        logger.info(
            "tool_outcome",
            extra={
                "tool": "ingest_prescription_multi",
                "status": "ok",
                "s3_key": loc.s3_key,
                "num_items": len(result_list or []),
            },
        )
        return {
            "status": "ok",
            "s3_bucket": loc.s3_bucket,
            "s3_key": loc.s3_key,
            "items": [r.dict() for r in (result_list or [])],
        }
    except Exception as exc:  # pragma: no cover
        logger.exception(
            "tool_outcome",
            extra={
                "tool": "ingest_prescription_multi",
                "status": "error",
                "error": str(exc),
            },
        )
        return {"error": "ingest_multi_failed"}
