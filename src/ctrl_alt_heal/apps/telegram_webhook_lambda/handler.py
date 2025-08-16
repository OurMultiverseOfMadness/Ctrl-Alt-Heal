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
    materialize_prescriptions_from_bundle,
    to_fhir_bundle,
)
from ...interface.telegram.handlers.router import parse_command
from ...shared.infrastructure.fhir_store import FhirStore
from ...shared.infrastructure.identities import (
    get_identity_by_telegram,
    link_telegram_user,
    upsert_phone_for_telegram,
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


def _send_message(
    chat_id: int,
    text: str,
    settings: Settings,
    reply_markup: dict[str, Any] | None = None,
    reply_to_message_id: int | None = None,
) -> None:
    token = _get_bot_token(settings)
    url = f"{settings.telegram_api_url}/bot{token}/sendMessage"
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    if reply_to_message_id is not None:
        payload["reply_to_message_id"] = reply_to_message_id
    payload_bytes = _json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload_bytes, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except urllib.error.URLError:
        # Avoid failing webhook on send errors
        pass


def _answer_callback_query(callback_query_id: str, settings: Settings) -> None:
    token = _get_bot_token(settings)
    url = f"{settings.telegram_api_url}/bot{token}/answerCallbackQuery"
    payload_bytes = _json.dumps({"callback_query_id": callback_query_id}).encode(
        "utf-8"
    )
    req = urllib.request.Request(
        url, data=payload_bytes, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except urllib.error.URLError:
        pass


def _send_contact_request(chat_id: int, settings: Settings) -> None:
    token = _get_bot_token(settings)
    url = f"{settings.telegram_api_url}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": (
            "To personalize your reminders, please share your phone number. "
            "Tap the button below."
        ),
        "reply_markup": {
            "keyboard": [[{"text": "Share phone number", "request_contact": True}]],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        },
    }
    payload_bytes = _json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload_bytes, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except urllib.error.URLError:
        pass


def _ensure_phone(
    telegram_user_id: int | None, chat_id: int | None, settings: Settings
) -> bool:
    if not isinstance(telegram_user_id, int) or not isinstance(chat_id, int):
        return False
    try:
        ident = get_identity_by_telegram(telegram_user_id)
        phone = (ident or {}).get("phone") if ident else None
        if not phone:
            _send_contact_request(chat_id, settings)
            return False
        return True
    except Exception:
        return False


# Minimal in-memory FHIR samples for testing via buttons
SAMPLE_FHIR: dict[str, dict[str, object]] = {
    "fhir_sample_1": {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {"text": "Amoxicillin 500 mg"},
                    "dosageInstruction": [
                        {
                            "text": (
                                "Take 1 capsule by mouth three times daily for 7 days."
                            )
                        }
                    ],
                }
            }
        ],
    },
    "fhir_sample_2": {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {"text": "Metformin 500 mg"},
                    "dosageInstruction": [
                        {"text": "Take 1 tablet twice daily with meals."}
                    ],
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {"text": "Atorvastatin 20 mg"},
                    "dosageInstruction": [
                        {"text": "Take 1 tablet at night once daily."}
                    ],
                }
            },
        ],
    },
    "fhir_sample_3": {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {"text": "Albuterol Inhaler"},
                    "dosageInstruction": [
                        {"text": "Inhale 2 puffs every 4-6 hours as needed."}
                    ],
                }
            }
        ],
    },
    "fhir_sample_4": {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {"text": "Levothyroxine 75 mcg"},
                    "dosageInstruction": [
                        {
                            "text": (
                                "Take 1 tablet every morning on empty stomach "
                                "for 90 days."
                            )
                        }
                    ],
                }
            }
        ],
    },
}


def _handle_fhir_document(
    chat_id: int, update: dict[str, Any], settings: Settings
) -> None:
    s3 = boto3.client("s3")
    from ...interface.telegram.download import download_and_store_telegram_file

    loc = download_and_store_telegram_file(update, settings)
    obj = s3.get_object(Bucket=loc.s3_bucket, Key=loc.s3_key)
    data_bytes: bytes = obj["Body"].read()
    try:
        parsed = json.loads(data_bytes.decode("utf-8"))
    except Exception:
        parsed = {}
    if isinstance(parsed, dict) and parsed.get("resourceType") == "Bundle":
        to_store = parsed
    else:
        to_store = to_fhir_bundle(chat_id, parsed)
    try:
        store = FhirStore(settings.fhir_table_name)
        sk = store.save_bundle(chat_id, to_store)
        # materialize prescriptions for quick viewing
        materialize_prescriptions_from_bundle(chat_id, to_store, source_bundle_sk=sk)
        _send_message(
            chat_id, "FHIR record saved. I will set up reminders next.", settings
        )
    except Exception:
        logger = get_logger(__name__)
        logger.exception("fhir_save_error")
        _send_message(chat_id, "Sorry, failed to save FHIR data.", settings)


def _compose_single_summary(res: dict[str, Any]) -> str:
    data = res.get("extraction")
    # If the tool returned a string, try to parse it
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    if isinstance(data, dict):
        # Prefer the first medication if present
        medications = data.get("medications")
        med: dict[str, Any] | None = None
        if (
            isinstance(medications, list)
            and medications
            and isinstance(medications[0], dict)
        ):
            med = medications[0]
        elif all(k in data for k in ("name", "dosage")):
            med = data
        # Fallback: some models return { "medicine": {...} }
        if med is None and isinstance(data.get("medicine"), dict):
            med = data.get("medicine")
        if isinstance(med, dict):
            name = (
                med.get("name")
                or med.get("medication")
                or med.get("drug")
                or "(unknown)"
            )
            dose = med.get("dosage") or med.get("dose") or "(dose unknown)"
            freq_val = med.get("frequency")
            if isinstance(freq_val, dict):
                freq = (
                    freq_val.get("free_text")
                    or freq_val.get("text")
                    or "(frequency unknown)"
                )
            else:
                freq = freq_val or "(frequency unknown)"
            return (
                f"Parsed: {name} — {dose}, {freq}\n"
                "Is this correct? Reply 'yes' or 'no'."
            )
    return "Parsed the label. Is this correct? Reply 'yes' or 'no'."


def _compose_multi_summary(res: dict[str, Any]) -> str:
    items = res.get("items")
    if isinstance(items, list) and items:
        lines: list[str] = []
        for item in items[:5]:
            if isinstance(item, dict):
                name = (
                    item.get("name")
                    or item.get("medication")
                    or item.get("drug")
                    or "(unknown)"
                )
                dose = item.get("dosage") or item.get("dose") or "(dose unknown)"
                freq_val = item.get("frequency")
                if isinstance(freq_val, dict):
                    freq = (
                        freq_val.get("free_text")
                        or freq_val.get("text")
                        or "(frequency unknown)"
                    )
                else:
                    freq = freq_val or "(frequency unknown)"
                lines.append(f"- {name}: {dose}, {freq}")
        more = "" if len(items) <= 5 else f"\n(+{len(items) - 5} more)"
        body = "\n".join(lines) + more
        return f"Parsed medications:\n{body}\nIs this correct? Reply 'yes' or 'no'."
    return "Parsed the prescription. Is this correct? Reply 'yes' or 'no'."


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger = get_logger(__name__)
    logger.info("handler_start")
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
    callback_query = update.get("callback_query")
    if message and isinstance(message, dict):
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        logger.info("update_received")
        # Handle contact share for phone number linkage
        contact = message.get("contact")
        if isinstance(contact, dict):
            phone = contact.get("phone_number")
            from_user = message.get("from") or {}
            uid = from_user.get("id") if isinstance(from_user, dict) else None
            if isinstance(uid, int) and isinstance(phone, str) and phone:
                try:
                    upsert_phone_for_telegram(uid, phone)
                    if isinstance(chat_id, int):
                        _send_message(
                            chat_id, "Thank you! Phone number linked.", settings
                        )
                except Exception:
                    logger.exception("identity_phone_link_error")

    # Handle callback buttons (inline keyboard)
    if isinstance(callback_query, dict):
        try:
            data = callback_query.get("data")
            cb_msg = callback_query.get("message") or {}
            chat = (cb_msg.get("chat") or {}) if isinstance(cb_msg, dict) else {}
            cb_chat_id = chat.get("id")
            cb_message_id = (
                cb_msg.get("message_id") if isinstance(cb_msg, dict) else None
            )
            if isinstance(cb_chat_id, int):
                if data == "confirm_yes":
                    st = get_state(cb_chat_id)
                    extraction = st.get("last_extraction")
                    try:
                        bundle = to_fhir_bundle(
                            cb_chat_id, extraction if extraction else {}
                        )
                        store = FhirStore(settings.fhir_table_name)
                        store.save_bundle(cb_chat_id, bundle)
                    except Exception:
                        logger.exception("fhir_persist_error")
                    _send_message(
                        cb_chat_id, "Saved. I will set up reminders next.", settings
                    )
                    clear_state(cb_chat_id)
                elif data == "confirm_no":
                    _send_message(
                        cb_chat_id,
                        "Okay. Please type corrections (dose/frequency).",
                        settings,
                        reply_to_message_id=cb_message_id
                        if isinstance(cb_message_id, int)
                        else None,
                    )
                elif data == "upload_fhir":
                    cb_from = callback_query.get("from") or {}
                    uid = cb_from.get("id") if isinstance(cb_from, dict) else None
                    if not _ensure_phone(uid, cb_chat_id, settings):
                        return {"statusCode": 200, "body": "ok"}
                    st = get_state(cb_chat_id)
                    st["awaiting_fhir"] = True
                    set_state(cb_chat_id, st)
                    _send_message(
                        cb_chat_id,
                        (
                            "Please attach the FHIR JSON file here. I’ll read it and "
                            "create your medication schedule."
                        ),
                        settings,
                        reply_markup={
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "📄 Use sample FHIR 1",
                                        "callback_data": "fhir_sample_1",
                                    },
                                    {
                                        "text": "📄 Use sample FHIR 2",
                                        "callback_data": "fhir_sample_2",
                                    },
                                ],
                                [
                                    {
                                        "text": "📄 Use sample FHIR 3",
                                        "callback_data": "fhir_sample_3",
                                    },
                                    {
                                        "text": "📄 Use sample FHIR 4",
                                        "callback_data": "fhir_sample_4",
                                    },
                                ],
                            ]
                        },
                        reply_to_message_id=cb_message_id
                        if isinstance(cb_message_id, int)
                        else None,
                    )
                elif data in {
                    "fhir_sample_1",
                    "fhir_sample_2",
                    "fhir_sample_3",
                    "fhir_sample_4",
                }:
                    # Require phone before proceeding
                    cb_from = callback_query.get("from") or {}
                    uid = cb_from.get("id") if isinstance(cb_from, dict) else None
                    if not _ensure_phone(uid, cb_chat_id, settings):
                        return {"statusCode": 200, "body": "ok"}
                    sample = SAMPLE_FHIR.get(str(data)) or {}
                    try:
                        store = FhirStore(settings.fhir_table_name)
                        sk = store.save_bundle(cb_chat_id, sample)
                        # also materialize prescriptions for the sample bundle
                        materialize_prescriptions_from_bundle(
                            cb_chat_id, sample, source_bundle_sk=sk
                        )
                        _send_message(
                            cb_chat_id,
                            "Sample FHIR saved. I will set up reminders next.",
                            settings,
                        )
                    except Exception:
                        logger.exception("fhir_sample_save_error")
                        _send_message(
                            cb_chat_id, "Sorry, failed to save sample.", settings
                        )
                elif data == "rx_history_next":
                    st = get_state(cb_chat_id)
                    lek = st.get("rx_history_lek")
                    if lek:
                        try:
                            from ...shared.infrastructure.prescriptions_store import (
                                list_prescriptions_page,
                            )

                            items, next_lek = list_prescriptions_page(
                                cb_chat_id, limit=5, last_evaluated_key=lek
                            )
                            st["rx_history_lek"] = next_lek
                            set_state(cb_chat_id, st)
                            lines = [
                                (
                                    f"- {it.get('medicationName')}: "
                                    f"{it.get('dosageText') or ''}"
                                )
                                for it in items
                            ]
                            markup = (
                                {
                                    "inline_keyboard": [
                                        [
                                            {
                                                "text": "Next ▶",
                                                "callback_data": "rx_history_next",
                                            }
                                        ]
                                    ]
                                }
                                if next_lek
                                else {}
                            )
                            _send_message(
                                cb_chat_id,
                                "Your prescriptions (more):\n" + "\n".join(lines),
                                settings,
                                reply_markup=markup,
                            )
                        except Exception:
                            logger.exception("history_next_error")
                elif data == "rx_active_next":
                    st = get_state(cb_chat_id)
                    lek = st.get("rx_active_lek")
                    if lek:
                        try:
                            from ...shared.infrastructure.prescriptions_store import (
                                list_prescriptions_page,
                            )

                            items, next_lek = list_prescriptions_page(
                                cb_chat_id,
                                status="active",
                                limit=5,
                                last_evaluated_key=lek,
                            )
                            st["rx_active_lek"] = next_lek
                            set_state(cb_chat_id, st)
                            lines = [
                                (
                                    f"- {it.get('medicationName')}: "
                                    f"{it.get('dosageText') or ''}"
                                )
                                for it in items
                            ]
                            markup = (
                                {
                                    "inline_keyboard": [
                                        [
                                            {
                                                "text": "Next ▶",
                                                "callback_data": "rx_active_next",
                                            }
                                        ]
                                    ]
                                }
                                if next_lek
                                else {}
                            )
                            _send_message(
                                cb_chat_id,
                                "Active prescriptions (more):\n" + "\n".join(lines),
                                settings,
                                reply_markup=markup,
                            )
                        except Exception:
                            logger.exception("active_next_error")
                elif data == "set_source_label":
                    st = get_state(cb_chat_id)
                    file_update = st.get("last_file_update")
                    if isinstance(file_update, dict):
                        set_state(
                            cb_chat_id,
                            {"pending_correction": True, "source_type": "label"},
                        )
                        agent = StrandsAgent.default()
                        res = agent.handle_sdk(
                            "ingest_prescription_file", {"update": file_update}
                        )
                        if res.get("error"):
                            _send_message(
                                cb_chat_id,
                                "Sorry, I couldn't process that file.",
                                settings,
                            )
                        else:
                            summary = _compose_single_summary(res)
                            _send_message(cb_chat_id, summary, settings)
                            after = get_state(cb_chat_id)
                            after.pop("last_file_update", None)
                            after["last_extraction"] = res.get("extraction")
                            set_state(cb_chat_id, after)
                    else:
                        _send_message(
                            cb_chat_id, "Please send the label photo first.", settings
                        )
                elif data == "set_source_prescription":
                    st = get_state(cb_chat_id)
                    file_update = st.get("last_file_update")
                    if isinstance(file_update, dict):
                        set_state(
                            cb_chat_id,
                            {"pending_correction": True, "source_type": "prescription"},
                        )
                        agent = StrandsAgent.default()
                        res = agent.handle_sdk(
                            "ingest_prescription_multi", {"update": file_update}
                        )
                        if res.get("error"):
                            _send_message(
                                cb_chat_id,
                                "Sorry, I couldn't process that file.",
                                settings,
                            )
                        else:
                            summary = _compose_multi_summary(res)
                            _send_message(cb_chat_id, summary, settings)
                            after = get_state(cb_chat_id)
                            after.pop("last_file_update", None)
                            after["last_extraction"] = {"medications": res.get("items")}
                            set_state(cb_chat_id, after)
                    else:
                        _send_message(
                            cb_chat_id,
                            "Please send the prescription image first.",
                            settings,
                        )
            cb_id = callback_query.get("id")
            if isinstance(cb_id, str):
                _answer_callback_query(cb_id, settings)
        except Exception:
            logger.exception("auto_route_error")
        return {"statusCode": 200, "body": "ok"}

    # Prefer control-word handling and file-memory before generic routing
    try:
        if chat_id is not None and message:
            agent = StrandsAgent.default()
            has_doc = "document" in message
            has_photo = "photo" in message
            has_text = isinstance(message.get("text"), str)

            # If a file arrived with this update, remember it for next control word
            if has_doc or has_photo:
                current = get_state(chat_id)
                current["last_file_update"] = update
                set_state(chat_id, current)

            text_lower = (
                str(message.get("text", "")).strip().lower() if has_text else ""
            )
            state = get_state(chat_id)

            # Link identity (best-effort)
            try:
                from_user = message.get("from") or {}
                uid = from_user.get("id") if isinstance(from_user, dict) else None
                if isinstance(uid, int):
                    link_telegram_user(uid, phone=None, attrs={})
            except Exception:
                pass

            # Slash command handling (e.g., /start, /help)
            cmd, _args = parse_command(update)
            if cmd == "start":
                _send_message(
                    chat_id,
                    (
                        "Hi! I’m your recovery companion. I’ll help you follow your "
                        "medications on time and keep things simple.\n\n"
                        "Would you like to upload a prescription now? You can send a "
                        "photo of a label or prescription, or upload a FHIR record "
                        "from your hospital if you have one."
                    ),
                    settings,
                    reply_markup={
                        "inline_keyboard": [
                            [
                                {
                                    "text": "📷 Label (single)",
                                    "callback_data": "set_source_label",
                                },
                                {
                                    "text": "📝 Prescription (multi)",
                                    "callback_data": "set_source_prescription",
                                },
                            ],
                            [
                                {
                                    "text": "📄 Upload FHIR record",
                                    "callback_data": "upload_fhir",
                                }
                            ],
                        ]
                    },
                )
                # If identity lacks phone, ask for contact share
                try:
                    from_user = message.get("from") or {}
                    uid = from_user.get("id") if isinstance(from_user, dict) else None
                    if isinstance(uid, int):
                        ident = get_identity_by_telegram(uid)
                        phone = (ident or {}).get("phone") if ident else None
                        if not phone:
                            _send_contact_request(chat_id, settings)
                except Exception:
                    pass
                return {"statusCode": 200, "body": "ok"}
            if cmd == "help":
                _send_message(
                    chat_id,
                    (
                        "Here’s what I can do:\n"
                        "- Upload a label photo (single medicine) or a doctor’s "
                        "prescription (multiple).\n"
                        "- Upload a FHIR record from your hospital portal.\n"
                        "- List your prescriptions and see what’s active.\n"
                        "- Set up reminders (coming soon).\n\n"
                        "Commands:\n"
                        "/start — show the main menu\n"
                        "/help — this help\n"
                        "/history — recent prescriptions\n"
                        "/active — active prescriptions\n\n"
                        'Tip: You can also ask, e.g. "what are my active '
                        'prescriptions?"'
                    ),
                    settings,
                )
                return {"statusCode": 200, "body": "ok"}
            if cmd == "history":
                items = []
                try:
                    from ...shared.infrastructure.prescriptions_store import (
                        list_prescriptions_page,
                    )

                    items, lek = list_prescriptions_page(
                        int(chat_id) if isinstance(chat_id, int) else 0, limit=5
                    )
                    st = get_state(chat_id)
                    st["rx_history_lek"] = lek
                    set_state(chat_id, st)
                except Exception:
                    logger.exception("history_list_error")
                if not items:
                    _send_message(chat_id, "No prescriptions found.", settings)
                else:
                    lines: list[str] = []
                    for it in items[:5]:
                        lines.append(
                            f"- {it.get('medicationName')}: "
                            f"{it.get('dosageText') or ''}"
                        )
                    reply_markup = (
                        {
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "Next ▶",
                                        "callback_data": "rx_history_next",
                                    }
                                ]
                            ]
                        }
                        if st.get("rx_history_lek")
                        else {}
                    )
                    _send_message(
                        chat_id,
                        "Your prescriptions:\n" + "\n".join(lines),
                        settings,
                        reply_markup=reply_markup,
                    )
                return {"statusCode": 200, "body": "ok"}
            if cmd == "active":
                items = []
                try:
                    from ...shared.infrastructure.prescriptions_store import (
                        list_prescriptions_page,
                    )

                    items, lek = list_prescriptions_page(
                        int(chat_id) if isinstance(chat_id, int) else 0,
                        status="active",
                        limit=5,
                    )
                    st = get_state(chat_id)
                    st["rx_active_lek"] = lek
                    set_state(chat_id, st)
                except Exception:
                    logger.exception("active_list_error")
                if not items:
                    _send_message(chat_id, "No active prescriptions.", settings)
                else:
                    lines: list[str] = []
                    for it in items[:5]:
                        lines.append(
                            f"- {it.get('medicationName')}: "
                            f"{it.get('dosageText') or ''}"
                        )
                    reply_markup = (
                        {
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "Next ▶",
                                        "callback_data": "rx_active_next",
                                    }
                                ]
                            ]
                        }
                        if st.get("rx_active_lek")
                        else {}
                    )
                    _send_message(
                        chat_id,
                        "Active prescriptions:\n" + "\n".join(lines),
                        settings,
                        reply_markup=reply_markup,
                    )
                return {"statusCode": 200, "body": "ok"}

            # Control words: label / prescription / fhir
            if text_lower in {"label", "/label"}:
                logger.info("control_label")
                file_update = (
                    update if (has_doc or has_photo) else state.get("last_file_update")
                )
                if not isinstance(file_update, dict):
                    _send_message(
                        chat_id, "Please send the label photo first.", settings
                    )
                    return {"statusCode": 200, "body": "ok"}
                set_state(chat_id, {"pending_correction": True, "source_type": "label"})
                res = agent.handle_sdk(
                    "ingest_prescription_file", {"update": file_update}
                )
                if res.get("error"):
                    logger.warning("ingest_label_error")
                    _send_message(
                        chat_id, "Sorry, I couldn't process that file.", settings
                    )
                else:
                    summary = _compose_single_summary(res)
                    _send_message(
                        chat_id,
                        summary,
                        settings,
                        reply_markup={
                            "inline_keyboard": [
                                [
                                    {"text": "✅ Yes", "callback_data": "confirm_yes"},
                                    {
                                        "text": "✏️ No, correct",
                                        "callback_data": "confirm_no",
                                    },
                                ]
                            ]
                        },
                    )
                    # Save last extraction for commit on 'yes'
                    st = get_state(chat_id)
                    st["last_extraction"] = res.get("extraction")
                    set_state(chat_id, st)
                after = get_state(chat_id)
                after.pop("last_file_update", None)
                set_state(chat_id, after)
            elif text_lower in {"prescription", "/prescription"}:
                logger.info("control_prescription")
                file_update = (
                    update if (has_doc or has_photo) else state.get("last_file_update")
                )
                if not isinstance(file_update, dict):
                    _send_message(
                        chat_id, "Please send the prescription image first.", settings
                    )
                    return {"statusCode": 200, "body": "ok"}
                set_state(
                    chat_id, {"pending_correction": True, "source_type": "prescription"}
                )
                res = agent.handle_sdk(
                    "ingest_prescription_multi", {"update": file_update}
                )
                if res.get("error"):
                    logger.warning("ingest_prescription_error")
                    _send_message(
                        chat_id, "Sorry, I couldn't process that file.", settings
                    )
                else:
                    summary = _compose_multi_summary(res)
                    _send_message(
                        chat_id,
                        summary,
                        settings,
                        reply_markup={
                            "inline_keyboard": [
                                [
                                    {"text": "✅ Yes", "callback_data": "confirm_yes"},
                                    {
                                        "text": "✏️ No, correct",
                                        "callback_data": "confirm_no",
                                    },
                                ]
                            ]
                        },
                    )
                    st = get_state(chat_id)
                    st["last_extraction"] = {"medications": res.get("items")}
                    set_state(chat_id, st)
                after = get_state(chat_id)
                after.pop("last_file_update", None)
                set_state(chat_id, after)
            elif text_lower in {"fhir", "/fhir"}:
                _send_message(
                    chat_id,
                    (
                        "Please send your FHIR JSON file (export from your hospital "
                        "portal). I will read it and set up reminders for you."
                    ),
                    settings,
                )
                return {"statusCode": 200, "body": "ok"}
            elif text_lower in {"yes", "/yes"}:
                # Persist FHIR bundle
                st = get_state(chat_id)
                extraction = st.get("last_extraction")
                try:
                    bundle = to_fhir_bundle(chat_id, extraction if extraction else {})
                    store = FhirStore(settings.fhir_table_name)
                    store.save_bundle(chat_id, bundle)
                except Exception:
                    logger.exception("fhir_persist_error")
                _send_message(chat_id, "Saved. I will set up reminders next.", settings)
                clear_state(chat_id)
            elif state.get("awaiting_fhir") and (has_doc or has_photo):
                try:
                    _handle_fhir_document(int(chat_id), update, settings)
                except Exception:
                    logger.exception("fhir_upload_error")
                    _send_message(
                        int(chat_id), "Sorry, I couldn't read that file.", settings
                    )
                after2 = get_state(chat_id)
                after2.pop("awaiting_fhir", None)
                set_state(chat_id, after2)
            elif text_lower in {"no", "/no"}:
                _send_message(
                    chat_id, "Okay. Please type corrections (dose/frequency).", settings
                )
            elif (
                state.get("pending_correction")
                and has_text
                and not text_lower.startswith("/")
            ):
                # Corrections flow
                source_type = state.get("source_type")
                correction_text = str(message.get("text", ""))
                if source_type == "label":
                    prompt = (
                        "Summarize this medication as 'name — dose, frequency':\n"
                        f"{correction_text}"
                    )
                    out = agent.handle_sdk("chat", {"text": prompt})
                    reply = out.get("reply") or "Parsed. Is this correct? yes/no"
                    _send_message(
                        chat_id, f"{reply}\nIs this correct? yes/no", settings
                    )
                elif source_type == "prescription":
                    prompt = (
                        "Summarize all medications as a bullet list 'name: dose, "
                        f"frequency':\n{correction_text}"
                    )
                    out = agent.handle_sdk("chat", {"text": prompt})
                    reply = out.get("reply") or "Parsed. Is this correct? yes/no"
                    _send_message(
                        chat_id, f"{reply}\nIs this correct? yes/no", settings
                    )
            else:
                # If a file arrived without text, prompt classification
                if (has_doc or has_photo) and not has_text:
                    _send_message(
                        int(chat_id),
                        (
                            "Is this a pharmacy label (single) or a doctor's "
                            "prescription (multiple)?"
                        ),
                        settings,
                        reply_markup={
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "📷 Label (single)",
                                        "callback_data": "set_source_label",
                                    },
                                    {
                                        "text": "📝 Prescription (multi)",
                                        "callback_data": "set_source_prescription",
                                    },
                                ]
                            ]
                        },
                    )
                # If plain text with no control/correction, route to chat
                elif has_text and not text_lower.startswith("/"):
                    # Simple NLU for "what are my active prescriptions?"
                    tl = text_lower
                    if "active" in tl and (
                        "rx" in tl or "prescription" in tl or "med" in tl
                    ):
                        try:
                            from ...shared.infrastructure.prescriptions_store import (
                                list_prescriptions_page,
                            )

                            items, _ = list_prescriptions_page(
                                int(chat_id) if isinstance(chat_id, int) else 0,
                                status="active",
                                limit=5,
                            )
                            if not items:
                                _send_message(
                                    chat_id, "No active prescriptions.", settings
                                )
                            else:
                                lines = [
                                    (
                                        f"- {it.get('medicationName')}: "
                                        f"{it.get('dosageText') or ''}"
                                    )
                                    for it in items[:5]
                                ]
                                _send_message(
                                    chat_id,
                                    "Active prescriptions:\n" + "\n".join(lines),
                                    settings,
                                )
                            return {"statusCode": 200, "body": "ok"}
                        except Exception:
                            logger.exception("active_nlu_error")
                    out = agent.handle_sdk(
                        "chat", {"text": str(message.get("text", ""))}
                    )
                    reply = (
                        out.get("reply") or "How can I help with your recovery today?"
                    )
                    _send_message(int(chat_id), str(reply), settings)
            # Do not send any further replies in this invocation; suppress fallback
            return {"statusCode": 200, "body": "ok"}
    except Exception:
        logger.exception("auto_route_error")

    # Slash commands and warm greeting
    cmd, _args = parse_command(update)
    if cmd == "start":
        _send_message(
            int(chat_id) if isinstance(chat_id, int) else 0,
            (
                "Hi! I’m your recovery companion. I’ll help you follow your "
                "medications on time and keep things simple.\n\n"
                "Would you like to upload a prescription now? You can send a "
                "photo of a label or prescription, or upload a FHIR record from "
                "your hospital if you have one."
            ),
            settings,
            reply_markup={
                "inline_keyboard": [
                    [
                        {
                            "text": "📷 Label (single)",
                            "callback_data": "set_source_label",
                        },
                        {
                            "text": "📝 Prescription (multi)",
                            "callback_data": "set_source_prescription",
                        },
                    ],
                    [{"text": "📄 Upload FHIR record", "callback_data": "upload_fhir"}],
                    [
                        {
                            "text": "📄 Use sample FHIR 1",
                            "callback_data": "fhir_sample_1",
                        },
                        {
                            "text": "📄 Use sample FHIR 2",
                            "callback_data": "fhir_sample_2",
                        },
                    ],
                    [
                        {
                            "text": "📄 Use sample FHIR 3",
                            "callback_data": "fhir_sample_3",
                        },
                        {
                            "text": "📄 Use sample FHIR 4",
                            "callback_data": "fhir_sample_4",
                        },
                    ],
                ]
            },
        )
        return {"statusCode": 200, "body": "ok"}

    # Control words include FHIR
    if text_lower in {"fhir", "/fhir"}:
        _send_message(
            int(chat_id) if isinstance(chat_id, int) else 0,
            (
                "Please send your FHIR JSON file (export from your hospital "
                "portal). I will read it and set up reminders for you."
            ),
            settings,
        )
        return {"statusCode": 200, "body": "ok"}

    # When a document is received with intent FHIR
    if has_doc and text_lower in {"fhir", "/fhir"}:
        _handle_fhir_document(
            int(chat_id) if isinstance(chat_id, int) else 0, update, settings
        )
        return {"statusCode": 200, "body": "ok"}

    # Fallback suppressed to avoid duplicate replies during control flows

    return {"statusCode": 200, "body": "ok"}
