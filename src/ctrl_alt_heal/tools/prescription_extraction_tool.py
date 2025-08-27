from __future__ import annotations
from typing import Any

from strands import tool

from ctrl_alt_heal.config import settings
from ctrl_alt_heal.infrastructure.bedrock import Bedrock
from .prescription_extractor import ExtractionInput


@tool(
    name="prescription_extraction",
    description="Extracts prescription information from an image and stores it.",
    inputSchema={
        "type": "object",
        "properties": {
            "s3_bucket": {"type": "string"},
            "s3_key": {"type": "string"},
            "user_id": {"type": "string"},
        },
        "required": ["s3_bucket", "s3_key", "user_id"],
    },
)
def prescription_extraction_tool(
    s3_bucket: str, s3_key: str, user_id: str
) -> dict[str, Any]:
    """A tool for extracting prescription information from an image."""
    extractor = Bedrock(model_id=settings.bedrock_model_id)
    result = extractor.extract(
        ExtractionInput(
            user_id=user_id,
            s3_bucket=s3_bucket,
            s3_key=s3_key,
        )
    )
    return result.raw_json
