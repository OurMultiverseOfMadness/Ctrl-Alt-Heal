from __future__ import annotations

import json
import os
from dataclasses import dataclass

import boto3

from ...application.use_cases.extract_prescription import (
    ExtractionInput,
    ExtractionResult,
    PrescriptionExtractor,
)


@dataclass
class BedrockExtractor(PrescriptionExtractor):
    model_id: str
    region_name: str | None = None

    def extract(self, data: ExtractionInput) -> ExtractionResult:
        runtime = boto3.client(
            "bedrock-runtime",
            region_name=self.region_name
            or os.getenv("BEDROCK_REGION")
            or os.getenv("AWS_REGION"),
        )
        # Minimal prompt and schema placeholder
        prompt = {
            "inputText": (
                "Extract a structured medication plan as JSON with fields: "
                "medications:[{name,strength,unit,frequency,route,duration_days,start_date}],"
                "patient_name, doctor_name."
                f" Source: s3://{data.s3_bucket}/{data.s3_key}"
            )
        }
        body = json.dumps(prompt)
        resp = runtime.invoke_model(
            modelId=self.model_id,
            accept="application/json",
            contentType="application/json",
            body=body,
        )
        payload = resp["body"].read().decode()
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            parsed = {"raw": payload}
        return ExtractionResult(raw_json=parsed, confidence=0.5)
