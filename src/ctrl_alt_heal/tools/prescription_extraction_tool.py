from typing import Any

from strands import tool

from ctrl_alt_heal.infrastructure.bedrock import BedrockExtractor
from ctrl_alt_heal.tools.prescription_extractor import (
    ExtractionInput,
    extract_prescription,
)
from ctrl_alt_heal.config import settings


@tool(
    description="Extracts prescription information from an image.",
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
    extractor = BedrockExtractor(model_id=settings.bedrock_model_id)
    result = extract_prescription(
        extractor, ExtractionInput(s3_bucket=s3_bucket, s3_key=s3_key), user_id=user_id
    )
    return result.raw_json
