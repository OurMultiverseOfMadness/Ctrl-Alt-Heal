from __future__ import annotations

import json
import os
from typing import Any

import boto3

from ....config.settings import Settings
from ....shared.infrastructure.logger import get_logger


def chat_tool(payload: dict[str, Any]) -> dict[str, Any]:
    """Simple chat tool using Bedrock chat model.

    Expects: {"text": str, "context": Optional[dict]}
    Returns: {"reply": str}
    """
    logger = get_logger(__name__)
    settings = Settings.load()
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        return {"error": "empty_text"}

    model_id = settings.bedrock_chat_model_id or settings.bedrock_model_id
    region = settings.bedrock_region or settings.aws_region or os.getenv("AWS_REGION")
    runtime = boto3.client("bedrock-runtime", region_name=region)

    # Nova chat expects a messages array
    body = json.dumps(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": text.strip()}],
                }
            ]
        }
    )
    try:
        resp = runtime.invoke_model(
            modelId=model_id,
            accept="application/json",
            contentType="application/json",
            body=body,
        )
        payload_text = resp["body"].read().decode()
        # Best-effort parse for Nova chat responses
        try:
            data = json.loads(payload_text)
            # Try common fields
            reply = (
                (data.get("output") or {}).get("message")
                or data.get("outputText")
                or data.get("completion")
                or payload_text
            )
            if isinstance(reply, dict):
                # message may have content array
                content = reply.get("content")
                if (
                    isinstance(content, list)
                    and content
                    and isinstance(content[0], dict)
                ):
                    reply = content[0].get("text") or payload_text
        except json.JSONDecodeError:
            reply = payload_text
        return {"reply": str(reply)}
    except Exception as exc:  # pragma: no cover
        logger.exception("chat_tool_error", extra={"error": str(exc)})
        return {"error": "chat_failed"}
