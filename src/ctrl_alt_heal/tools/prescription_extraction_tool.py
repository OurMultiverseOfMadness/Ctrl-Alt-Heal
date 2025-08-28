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
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info(
            f"prescription_extraction_tool called with s3_bucket: {s3_bucket}, s3_key: {s3_key}, user_id: {user_id}"
        )

        extractor = Bedrock(model_id=settings.bedrock_multimodal_model_id)
        logger.info("Bedrock extractor created successfully")

        result = extract_prescription(
            extractor,
            ExtractionInput(s3_bucket=s3_bucket, s3_key=s3_key),
            user_id=user_id,
        )

        logger.info(f"extract_prescription returned: {result}")
        logger.info(f"result.prescriptions: {result.prescriptions}")

        # Return a structured dictionary with the results
        if result.prescriptions:
            prescription_data = [p.model_dump() for p in result.prescriptions]
            response = {
                "status": "success",
                "message": f"Successfully extracted {len(result.prescriptions)} prescription(s) from the image and saved them to your profile.",
                "prescriptions": prescription_data,
                "count": len(result.prescriptions),
                "extraction_summary": {
                    "total_medications": len(result.prescriptions),
                    "medication_names": [p.name for p in result.prescriptions],
                    "extraction_confidence": result.confidence or 0.5,
                },
            }
            logger.info(f"Returning success response: {response}")
            return response

        error_response = {
            "status": "error",
            "message": "No prescriptions were extracted from the image. Please ensure the image contains a clear prescription document.",
            "prescriptions": [],
            "count": 0,
        }
        logger.info(f"Returning error response: {error_response}")
        return error_response

    except Exception as e:
        logger.error(f"Exception in prescription_extraction_tool: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "message": f"An error occurred while extracting prescription: {str(e)}",
            "prescriptions": [],
            "count": 0,
        }
