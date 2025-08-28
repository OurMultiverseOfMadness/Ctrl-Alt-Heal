from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, ClassVar
import copy

import boto3
import logging

from ctrl_alt_heal.tools.prescription_extractor import (
    ExtractionInput,
    ExtractionResult,
    PrescriptionExtractor,
)
from ctrl_alt_heal.domain.models import Prescription


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

        prompt_text = (
            "Extract medications as JSON: "
            "medications:[{name,dosage,frequency,route,duration_days}], "
            "patient_name, doctor_name."
        )
        system_prompt = (
            "You are a clinical pharmacist. "
            "Reply ONLY valid JSON. "
            "Schema: {medications:[{name:string,dosage:string,"
            "frequency:string,route?:string,"
            "duration_days?:number}],"
            "patient_name?:string,doctor_name?:string}."
        )
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": image_format,
                                "source": {"bytes": img_bytes},
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
                redacted = copy.deepcopy(request_body)
                redacted["messages"][0]["content"][0]["image"]["source"]["bytes"] = (
                    "<redacted>"
                )
                preview = json.dumps(redacted)[:2000]
                logger.info("bedrock_io_input preview=%s", preview)
            except Exception:
                logger.info("bedrock_io_input")

        logger.info("bedrock_invoke")
        try:
            resp = runtime.converse(
                modelId=self.model_id,
                system=[{"text": system_prompt}],
                messages=request_body["messages"],
                inferenceConfig=request_body["inferenceConfig"],
            )
            payload = resp["output"]["message"]["content"][0]["text"]
            if os.getenv("BEDROCK_DEBUG_IO") == "1":
                logger.info(
                    "bedrock_io_output preview=%s len=%d", payload[:2000], len(payload)
                )
            # Parse Nova response and extract the assistant text which should be JSON
            extracted: dict[str, Any] | None = None
            try:
                text_blob = payload
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
                    extracted = {"raw": payload}
                logger.info(f"Extracted prescription data: {extracted}")
            except Exception:
                extracted = {"raw": payload}

            # Manually parse the raw JSON to create Prescription objects
            prescriptions = []
            if extracted and "medications" in extracted:
                prescription_list = extracted["medications"]
                if isinstance(prescription_list, list):
                    # Get the set of valid field names from the Prescription model
                    valid_fields = set(Prescription.model_fields.keys())
                    for p_data in prescription_list:
                        # Filter the dictionary from the LLM to only include valid fields
                        filtered_data = {
                            k: v for k, v in p_data.items() if k in valid_fields
                        }
                        # Capture any extra fields
                        extra_fields = {
                            k: v for k, v in p_data.items() if k not in valid_fields
                        }
                        if extra_fields:
                            filtered_data["extra_fields"] = extra_fields

                        # Ensure required fields have defaults if missing
                        if "totalAmount" not in filtered_data:
                            filtered_data["totalAmount"] = "Not specified"
                        if "dosage" not in filtered_data or not filtered_data["dosage"]:
                            filtered_data["dosage"] = "Not specified"
                        if (
                            "frequency" not in filtered_data
                            or not filtered_data["frequency"]
                        ):
                            filtered_data["frequency"] = "Not specified"

                        # Pydantic will validate the data here
                        prescriptions.append(Prescription(**filtered_data))

            return ExtractionResult(
                raw_json=extracted, confidence=0.5, prescriptions=prescriptions
            )
        except Exception:  # pragma: no cover
            logger.exception("bedrock_invoke_error")
            raise
