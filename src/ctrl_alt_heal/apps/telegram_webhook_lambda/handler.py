from __future__ import annotations

import json
import json as _json
import os
import urllib.error
import urllib.request
from typing import Any

import boto3

from ...agents.strands.agent import StrandsAgent
from ...config.settings import Settings
from ...shared.infrastructure.logger import get_logger


def _get_secret(arn: str | None) -> str | None:
    if not arn:
        return None
    sm = boto3.client("secretsmanager")
    try:
        get = sm.get_secret_value(SecretId=arn)
        val = get.get("SecretString")
        return str(val) if isinstance(val, str) else None
    except Exception:
        return None


def _get_bot_token(settings: Settings) -> str:
    token = settings.telegram_bot_token
    if not token:
        token = _get_secret(settings.telegram_bot_token_secret_arn) or ""
    if not token:
        raise RuntimeError("Telegram bot token not configured")
    return token


def _send_message(chat_id: int, text: str, settings: Settings) -> None:
    token = _get_bot_token(settings)
    url = f"{settings.telegram_api_url}/bot{token}/sendMessage"
    payload_bytes = _json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload_bytes, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except urllib.error.URLError:
        # Avoid failing webhook on send errors
        pass


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger = get_logger(__name__)
    settings = Settings.load()

    # Validate webhook secret (if present)
    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET") or _get_secret(
        settings.telegram_webhook_secret_arn
    )
    if secret:
        headers = event.get("headers") or {}
        token = headers.get("x-telegram-bot-api-secret-token") or headers.get(
            "X-Telegram-Bot-Api-Secret-Token"
        )
        if token != secret:
            logger.warning("webhook_auth_failed")
            return {"statusCode": 403, "body": "forbidden"}

    try:
        update = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        logger.warning("invalid_json_body")
        return {"statusCode": 400, "body": "invalid json"}

    chat_id: int | None = None
    message = update.get("message") or update.get("edited_message")
    if message and isinstance(message, dict):
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        logger.info(
            "update_received",
            extra={
                "has_document": bool("document" in message),
                "has_photo": bool("photo" in message),
                "has_text": bool("text" in message),
            },
        )

    # Delegate everything to Strands auto-router and send the reply
    try:
        if chat_id is not None and message:
            agent = StrandsAgent.default()
            out = agent.handle("auto", {"update": update})
            reply = out.get("reply")
            if isinstance(reply, str) and reply:
                _send_message(chat_id, reply, settings)
            # If user replies 'label' or 'prescription', route accordingly
            if isinstance(message.get("text"), str):
                text_lower = str(message.get("text")).strip().lower()
                if text_lower in {"label", "/label"}:
                    res = agent.handle("ingest_prescription_file", {"update": update})
                    confirm = (
                        "Got your label. I will parse it and set up reminders."
                        if not res.get("error")
                        else "Sorry, I couldn't process that file."
                    )
                    _send_message(chat_id, confirm, settings)
                elif text_lower in {"prescription", "/prescription"}:
                    res = agent.handle("ingest_prescription_multi", {"update": update})
                    confirm = (
                        "Got your prescription. I will parse all medications."
                        if not res.get("error")
                        else "Sorry, I couldn't process that file."
                    )
                    _send_message(chat_id, confirm, settings)
    except Exception as exc:
        logger.exception("auto_route_error", extra={"error": str(exc)})

    # For plain text (non-command), route to chat tool via Strands
    if (
        chat_id is not None
        and message
        and "text" in message
        and not str(message.get("text", "")).startswith("/")
    ):
        agent = StrandsAgent.default()
        out = agent.handle("chat", {"text": str(message.get("text", ""))})
        reply = out.get("reply") or "How can I help with your recovery today?"
        logger.info("text_routed_to_chat")
        _send_message(chat_id, str(reply), settings)

    return {"statusCode": 200, "body": "ok"}
