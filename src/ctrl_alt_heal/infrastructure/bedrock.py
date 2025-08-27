from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from typing import Any, ClassVar

import boto3
import logging

from ctrl_alt_heal.tools.prescription_extractor import (
    ExtractionInput,
    ExtractionResult,
    PrescriptionExtractor,
)


@dataclass
class Bedrock(PrescriptionExtractor):
    _instances: ClassVar[dict[str, "Bedrock"]] = {}
    model_id: str
    region_name: str | None = None

    def extract(self, data: ExtractionInput) -> ExtractionResult:
        logger = logging.getLogger(__name__)
        resolved_region = (
            self.region_name or os.getenv("BEDROCK_REGION") or os.getenv("AWS_REGION")
        )
        runtime = boto3.client("bedrock-runtime", region_name=resolved_region)
        # Fetch image from S3 and embed as bytes for Nova multimodal
        s3 = boto3.client("s3")
        head = s3.head_object(Bucket=data.s3_bucket, Key=data.s3_key)
        content_type = (head.get("ContentType") or "").lower()
        if "png" in content_type:
            image_format = "png"
        elif "jpg" in content_type or "jpeg" in content_type:
            image_format = "jpeg"
        else:
            image_format = "jpeg"
        obj = s3.get_object(Bucket=data.s3_bucket, Key=data.s3_key)
        img_bytes = obj["Body"].read()
        b64 = base64.b64encode(img_bytes).decode("ascii")

        prompt_text = (
            "Extract medications as JSON: "
            "medications:[{name,dosage,frequency,route,duration_days}], "
            "patient_name, doctor_name."
        )
        request_body = {
            # Nova: supply system instruction via top-level "system" key,
            # do not use a "system" role inside messages.
            "system": [
                {
                    "text": (
                        "You are a clinical pharmacist. "
                        "Reply ONLY valid JSON. "
                        "Schema: {medications:[{name:string,dosage:string,"
                        "frequency:string,route?:string,"
                        "duration_days?:number}],"
                        "patient_name?:string,doctor_name?:string}."
                    )
                }
            ],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": image_format,
                                "source": {"bytes": b64},
                            }
                        },
                        {"text": prompt_text},
                    ],
                }
            ],
            "inferenceConfig": {"maxTokens": 400, "temperature": 0.2},
        }

        # Optional debug logging of Bedrock inputs (sanitized)
        if os.getenv("BEDROCK_DEBUG_IO") == "1":
            try:
                redacted = json.loads(json.dumps(request_body))
                redacted["messages"][0]["content"][0]["image"]["source"]["bytes"] = (
                    "<redacted>"
                )
                preview = json.dumps(redacted)[:2000]
                logger.info("bedrock_io_input preview=%s", preview)
            except Exception:
                logger.info("bedrock_io_input")

        body = json.dumps(request_body)
        logger.info("bedrock_invoke")
        try:
            resp = runtime.invoke_model(
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json",
                body=body,
            )
            payload = resp["body"].read().decode()
            if os.getenv("BEDROCK_DEBUG_IO") == "1":
                logger.info(
                    "bedrock_io_output preview=%s len=%d", payload[:2000], len(payload)
                )
            # Parse Nova response and extract the assistant text which should be JSON
            extracted: dict[str, Any] | None = None
            try:
                outer = json.loads(payload)
                content = (
                    (outer.get("output") or {}).get("message", {}).get("content", [])
                )
                text_blob: str | None = None
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and isinstance(part.get("text"), str):
                            text_blob = part.get("text")
                            break
                if isinstance(text_blob, str):
                    try:
                        extracted = json.loads(text_blob)
                    except json.JSONDecodeError:
                        # Fallback: try naive brace slice
                        first = text_blob.find("{")
                        last = text_blob.rfind("}")
                        if first != -1 and last != -1 and last > first:
                            inner = text_blob[first : last + 1]
                            try:
                                extracted = json.loads(inner)
                            except Exception:
                                pass
                if extracted is None:
                    extracted = outer
            except Exception:
                extracted = {"raw": payload}
            return ExtractionResult(raw_json=extracted, confidence=0.5)
        except Exception:  # pragma: no cover
            logger.exception("bedrock_invoke_error")
            raise
