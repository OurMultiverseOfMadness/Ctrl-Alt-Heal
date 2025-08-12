from __future__ import annotations

import json
import os
from typing import Any

import boto3


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # Minimal AWS Lambda handler stub for Telegram webhook.
    # Validates basic shape and returns 200 to satisfy Telegram retries.
    # Load webhook secret from Secrets Manager if ARN provided
    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
    secret_arn = os.environ.get("TELEGRAM_WEBHOOK_SECRET_ARN")
    if secret_arn:
        sm = boto3.client("secretsmanager")
        try:
            get = sm.get_secret_value(SecretId=secret_arn)
            secret = get.get("SecretString", secret)
        except Exception:
            pass
    if secret:
        # For HTTP API v2 payloads, headers are under event['headers']
        headers = event.get("headers") or {}
        token = headers.get("x-telegram-bot-api-secret-token") or headers.get(
            "X-Telegram-Bot-Api-Secret-Token"
        )
        if token != secret:
            return {"statusCode": 403, "body": "forbidden"}
    try:
        _ = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": "invalid json"}
    return {"statusCode": 200, "body": "ok"}
