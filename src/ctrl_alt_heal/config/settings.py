from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    aws_region: str
    bedrock_model_id: str
    fhir_server_url: str | None = None

    @staticmethod
    def load() -> Settings:
        return Settings(
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            aws_region=os.environ.get("AWS_REGION", "us-east-1"),
            bedrock_model_id=os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-1"),
            fhir_server_url=os.environ.get("FHIR_SERVER_URL"),
        )
