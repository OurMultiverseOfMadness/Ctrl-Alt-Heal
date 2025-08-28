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
            "Extract medications from this prescription image as JSON. "
            "For each medication, extract: name, dosage (amount per dose), "
            "frequency (how often to take), duration_days (total days of treatment), "
            "totalAmount (total quantity dispensed), and additionalInstructions (special notes)."
        )
        system_prompt = (
            "You are a clinical pharmacist extracting prescription data. "
            "Reply ONLY valid JSON with NO additional text. "
            "Schema: {"
            '"medications":['
            "{"
            '"name":"string (medication name)",'
            "\"dosage\":\"string (e.g. '1 tablet', '500mg', '2 capsules')\","
            "\"frequency\":\"string (e.g. 'twice daily', 'every 8 hours', 'as needed')\","
            '"duration_days":number (total treatment days, or null if not specified),'
            "\"totalAmount\":\"string (e.g. '30 tablets', '100ml bottle', 'sufficient quantity')\","
            "\"additionalInstructions\":\"string (e.g. 'take with food', 'avoid alcohol') or null\""
            "}"
            "],"
            '"patient_name":"string or null",'
            '"doctor_name":"string or null"'
            "}"
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

            # Look for prescription data under various possible keys
            prescription_list = None
            possible_keys = [
                "medications",
                "prescriptions",
                "drugs",
                "medicines",
                "medication_list",
                "prescription_list",
            ]

            if extracted:
                for key in possible_keys:
                    if key in extracted and extracted[key]:
                        prescription_list = extracted[key]
                        break

            if prescription_list:
                if isinstance(prescription_list, list):
                    for p_data in prescription_list:
                        # Create a more flexible mapping to handle AI variations
                        mapped_data = {}
                        extra_fields = {}

                        # Map common variations to our expected field names
                        field_mappings = {
                            "name": [
                                "name",
                                "medication",
                                "drug",
                                "medicine",
                                "medication_name",
                                "drug_name",
                            ],
                            "dosage": [
                                "dosage",
                                "dose",
                                "amount",
                                "strength",
                                "dosage_amount",
                            ],
                            "frequency": [
                                "frequency",
                                "freq",
                                "times",
                                "schedule",
                                "how_often",
                                "frequency_text",
                            ],
                            "duration_days": [
                                "duration_days",
                                "duration",
                                "days",
                                "period",
                                "length",
                            ],
                            "totalAmount": [
                                "totalAmount",
                                "total_amount",
                                "total",
                                "quantity",
                                "qty",
                                "amount_dispensed",
                            ],
                            "additionalInstructions": [
                                "additionalInstructions",
                                "additional_instructions",
                                "instructions",
                                "notes",
                                "directions",
                                "special_instructions",
                            ],
                        }

                        # Try to map AI output to our expected fields
                        for target_field, possible_keys in field_mappings.items():
                            for key in possible_keys:
                                if key in p_data and p_data[key]:
                                    mapped_data[target_field] = str(p_data[key])
                                    break

                        # Collect any unmapped fields as extra
                        mapped_keys = set()
                        for possible_keys in field_mappings.values():
                            mapped_keys.update(possible_keys)

                        for k, v in p_data.items():
                            if k not in mapped_keys:
                                extra_fields[k] = v

                        if extra_fields:
                            mapped_data["extra_fields"] = extra_fields

                        # Ensure required fields have defaults if missing
                        if "name" not in mapped_data or not mapped_data["name"]:
                            mapped_data["name"] = "Unknown medication"
                        if "dosage" not in mapped_data or not mapped_data["dosage"]:
                            mapped_data["dosage"] = "Not specified"
                        if (
                            "frequency" not in mapped_data
                            or not mapped_data["frequency"]
                        ):
                            mapped_data["frequency"] = "Not specified"
                        if (
                            "totalAmount" not in mapped_data
                            or not mapped_data["totalAmount"]
                        ):
                            mapped_data["totalAmount"] = "Not specified"

                        # Pydantic will validate the data here
                        prescriptions.append(Prescription(**mapped_data))

            return ExtractionResult(
                raw_json=extracted, confidence=0.5, prescriptions=prescriptions
            )
        except Exception:  # pragma: no cover
            logger.exception("bedrock_invoke_error")
            raise
