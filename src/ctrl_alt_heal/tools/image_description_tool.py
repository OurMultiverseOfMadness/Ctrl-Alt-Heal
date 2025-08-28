from __future__ import annotations

from typing import Any

import boto3
from strands import tool
import logging

# Initialize AWS clients
s3_client = boto3.client("s3")
bedrock_runtime_client = boto3.client("bedrock-runtime", region_name="ap-southeast-1")
logger = logging.getLogger(__name__)


@tool(
    name="describe_image",
    description=(
        "Use this tool to get a text description of an image stored in S3. "
        "This should be your FIRST step when a user uploads any image, to determine if it is a prescription, "
        "a lab result, or something else entirely. The description will guide your next action."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "s3_bucket": {
                "type": "string",
                "description": "The S3 bucket where the image is stored.",
            },
            "s3_key": {
                "type": "string",
                "description": "The S3 key (path) to the image file.",
            },
            "user_id": {
                "type": "string",
                "description": "The user id of the user who uploaded the image.",
            },
        },
        "required": ["s3_bucket", "s3_key", "user_id"],
    },
)
def describe_image_tool(s3_bucket: str, s3_key: str, user_id: str) -> dict[str, Any]:
    """
    Describes an image in S3 using a multi-modal model on Bedrock.
    """
    logger.info(
        f"describe_image_tool invoked with s3_bucket: '{s3_bucket}', s3_key: '{s3_key}', user_id: '{user_id}'"
    )
    try:
        # 1. Get the image from S3
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        image_bytes = response["Body"].read()

        # 2. Prepare the prompt for the multi-modal model (Amazon Nova Lite)
        prompt = (
            "Describe this image in detail. Pay close attention to any text. "
            "Is this a medical document, like a prescription or a lab report? "
            "If it is, what kind of document is it? If it is not, describe what it is."
        )

        # 3. Use the Converse API for multi-modal requests
        model_id = "apac.amazon.nova-lite-v1:0"

        response = bedrock_runtime_client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"image": {"format": "jpeg", "source": {"bytes": image_bytes}}},
                        {"text": prompt},
                    ],
                }
            ],
            inferenceConfig={"maxTokens": 2048, "temperature": 0.5},
        )

        # 4. Extract and return the description
        description = response["output"]["message"]["content"][0]["text"]
        return {
            "status": "success",
            "description": description,
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "user_id": user_id,
        }

    except s3_client.exceptions.NoSuchKey:
        return {
            "status": "error",
            "message": f"The file '{s3_key}' was not found in the bucket '{s3_bucket}'.",
        }
    except Exception as e:
        return {"status": "error", "message": f"An error occurred: {str(e)}"}
