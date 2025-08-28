from __future__ import annotations
from typing import Any

from strands import tool

from ctrl_alt_heal.config import settings
from ctrl_alt_heal.infrastructure.bedrock import Bedrock
from .prescription_extractor import extract_prescription, ExtractionInput


@tool(
    name="prescription_extraction",
    description=(
        "Use this tool ONLY after you have already confirmed that an image contains a prescription by using the 'describe_image' tool first. "
        "This tool extracts structured prescription details from an image file in an S3 bucket and stores them."
    ),
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
    extractor = Bedrock(model_id=settings.bedrock_multimodal_model_id)
    result = extract_prescription(
        extractor,
        ExtractionInput(s3_bucket=s3_bucket, s3_key=s3_key),
        user_id=user_id,
    )

    # Return a structured dictionary with the results
    if result.prescriptions:
        return {
            "status": "success",
            "prescriptions": [p.model_dump() for p in result.prescriptions],
        }
    return {"status": "error", "message": "No prescriptions were extracted."}
