from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    aws_region: str
    bedrock_model_id: str
    fhir_server_url: str | None = None
    bedrock_region: str | None = None
    bedrock_chat_model_id: str | None = None
    bedrock_extract_model_id: str | None = None

    # Telegram + Secrets
    telegram_api_url: str = "https://api.telegram.org"
    telegram_bot_token_secret_arn: str | None = None
    telegram_webhook_secret_arn: str | None = None

    # Storage
    docs_bucket: str | None = None

    # Scheduler wiring
    schedule_group: str = "ctrl-alt-heal-reminders"
    reminder_target_arn: str | None = None
    scheduler_role_arn: str | None = None

    @staticmethod
    def load() -> Settings:
        return Settings(
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            aws_region=os.environ.get("AWS_REGION", "us-east-1"),
            bedrock_model_id=os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-1"),
            fhir_server_url=os.environ.get("FHIR_SERVER_URL"),
            bedrock_region=os.environ.get("BEDROCK_REGION"),
            bedrock_chat_model_id=os.environ.get(
                "BEDROCK_CHAT_MODEL_ID", "amazon.nova-lite-v1"
            ),
            bedrock_extract_model_id=os.environ.get(
                "BEDROCK_EXTRACT_MODEL_ID", "amazon.nova-pro-v1"
            ),
            telegram_api_url=os.environ.get(
                "TELEGRAM_API_URL", "https://api.telegram.org"
            ),
            telegram_bot_token_secret_arn=os.environ.get(
                "TELEGRAM_BOT_TOKEN_SECRET_ARN"
            ),
            telegram_webhook_secret_arn=os.environ.get("TELEGRAM_WEBHOOK_SECRET_ARN"),
            docs_bucket=os.environ.get("DOCS_BUCKET"),
            schedule_group=os.environ.get("SCHEDULE_GROUP", "ctrl-alt-heal-reminders"),
            reminder_target_arn=os.environ.get("REMINDER_TARGET_ARN"),
            scheduler_role_arn=os.environ.get("SCHEDULER_ROLE_ARN"),
        )
