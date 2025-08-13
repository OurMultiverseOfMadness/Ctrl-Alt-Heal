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
from ...contexts.prescriptions.application.use_cases.extract_prescription import (
    extract_prescription,
    extract_prescriptions_list,
)
from ...shared.infrastructure.logger import get_logger
from ...shared.infrastructure.state_store import clear_state, get_state, set_state


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


def _compose_single_summary(res: dict[str, Any]) -> str:
    data = res.get("extraction")
    if isinstance(data, dict):
        # Try common shapes
        med = None
        meds = (
            data.get("medications")
            if isinstance(data.get("medications"), list)
            else None
        )
        if meds and isinstance(meds, list) and meds and isinstance(meds[0], dict):
            med = meds[0]
        else:
            med = data
        if isinstance(med, dict):
            name = med.get("name") or med.get("medication") or "(unknown)"
            dose = med.get("dosage") or med.get("dose") or "(dose unknown)"
            freq = (
                med.get("frequency") or (med.get("frequency") or {}).get("free_text")
                if isinstance(med.get("frequency"), dict)
                else None
            ) or "(frequency unknown)"
            return (
                f"Parsed: {name} — {dose}, {freq}\n"
                "Is this correct? Reply 'yes' or 'no'."
            )
    return "Parsed the label. Is this correct? Reply 'yes' or 'no'."


def _compose_multi_summary(res: dict[str, Any]) -> str:
    items = res.get("items")
    if isinstance(items, list) and items:
        lines: list[str] = []
        for item in items[:3]:
            if isinstance(item, dict):
                name = item.get("name") or "(unknown)"
                dose = item.get("dosage") or "(dose unknown)"
                freq = item.get("frequency") or "(frequency unknown)"
                lines.append(f"- {name}: {dose}, {freq}")
        more = "" if len(items) <= 3 else f"\n(+{len(items)-3} more)"
        body = "\n".join(lines) + more
        return f"Parsed medications:\n{body}\nIs this correct? Reply 'yes' or 'no'."
    return "Parsed the prescription. Is this correct? Reply 'yes' or 'no'."


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
                state = get_state(chat_id)
                if text_lower in {"label", "/label"}:
                    set_state(
                        chat_id, {"pending_correction": True, "source_type": "label"}
                    )
                    res = agent.handle("ingest_prescription_file", {"update": update})
                    if res.get("error"):
                        _send_message(
                            chat_id, "Sorry, I couldn't process that file.", settings
                        )
                    else:
                        summary = _compose_single_summary(res)
                        _send_message(chat_id, summary, settings)
                elif text_lower in {"prescription", "/prescription"}:
                    set_state(
                        chat_id,
                        {"pending_correction": True, "source_type": "prescription"},
                    )
                    res = agent.handle("ingest_prescription_multi", {"update": update})
                    if res.get("error"):
                        _send_message(
                            chat_id, "Sorry, I couldn't process that file.", settings
                        )
                    else:
                        summary = _compose_multi_summary(res)
                        _send_message(chat_id, summary, settings)
                elif text_lower in {"yes", "/yes"}:
                    _send_message(
                        chat_id, "Great! I will set up reminders next.", settings
                    )
                    clear_state(chat_id)
                elif text_lower in {"no", "/no"}:
                    _send_message(
                        chat_id,
                        "Okay. Please type corrections (dose/frequency).",
                        settings,
                    )
                elif state.get("pending_correction") and not text_lower.startswith("/"):
                    # Treat text as corrections and re-run appropriate extractor
                    source_type = state.get("source_type")
                    if source_type == "label":
                        model = extract_prescription(
                            summary=str(message.get("text", ""))
                        )
                        if model is None:
                            _send_message(
                                chat_id, "Sorry, I couldn't process that.", settings
                            )
                        else:
                            res = {"extraction": model.model_dump()}  # type: ignore[attr-defined]
                            _send_message(
                                chat_id, _compose_single_summary(res), settings
                            )
                    elif source_type == "prescription":
                        models = extract_prescriptions_list(
                            summary=str(message.get("text", ""))
                        )
                        if not models:
                            _send_message(
                                chat_id, "Sorry, I couldn't process that.", settings
                            )
                        else:
                            items = [m.model_dump() for m in models]  # type: ignore[attr-defined]
                            res = {"items": items}
                            _send_message(
                                chat_id, _compose_multi_summary(res), settings
                            )
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
