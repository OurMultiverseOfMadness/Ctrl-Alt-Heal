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
    upsert_language_for_telegram,
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
    # Optional translation via SEA LION if user prefers a non-English language
    try:
        ident = get_identity_by_telegram(int(chat_id)) or {}
        attrs = ident.get("attrs") if isinstance(ident, dict) else None
        lang = attrs.get("language") if isinstance(attrs, dict) else None
        lang_code = str(lang) if isinstance(lang, str) and lang else "en"
        if lang_code != "en":
            api_secret = _get_secret(settings.sealion_secret_arn)
            if api_secret:
                try:
                    import json as _json2
                    from urllib.request import Request, urlopen

                    body = {
                        "model": "aisingapore/Llama-SEA-LION-v3.5-8B-R",
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are a translator for patient-friendly health "
                                    "messages. Translate into the user's language, "
                                    "but preserve medicine names in English (do not "
                                    "translate drug names)."
                                ),
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"Target language code: {lang_code}. Text: {text}"
                                ),
                            },
                        ],
                    }
                    req = Request(
                        "https://api.sea-lion.ai/v1/chat/completions",
                        data=_json2.dumps(body).encode("utf-8"),
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {api_secret}",
                            "accept": "text/plain",
                        },
                        method="POST",
                    )
                    with urlopen(req, timeout=6) as resp:
                        payload_text = resp.read().decode("utf-8")
                        try:
                            parsed = _json2.loads(payload_text)
                            choices = (
                                parsed.get("choices")
                                if isinstance(parsed, dict)
                                else None
                            )
                            if isinstance(choices, list) and choices:
                                msg = (
                                    choices[0].get("message")
                                    if isinstance(choices[0], dict)
                                    else None
                                )
                                content = (
                                    msg.get("content")
                                    if isinstance(msg, dict)
                                    else None
                                )
                                if isinstance(content, str) and content:
                                    text = content
                        except Exception:
                            pass
                except Exception:
                    pass
    except Exception:
        pass

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
        # Auto-schedule reminders for newly materialized prescriptions
        created_msg = _auto_schedule_new_reminders(chat_id, settings)
        _send_message(
            chat_id,
            (
                "FHIR record saved. I have set up reminders: \n"
                + created_msg
                + "\nUse /reminders to view or cancel, or send new times to update."
            ),
            settings,
        )
    except Exception:
        logger = get_logger(__name__)
        logger.exception("fhir_save_error")
        _send_message(chat_id, "Sorry, failed to save FHIR data.", settings)


def _tz_label(chat_id: int) -> str:
    try:
        from ...shared.infrastructure.identities import get_identity_by_telegram

        ident_any = get_identity_by_telegram(int(chat_id))
        ident_dict: dict[str, Any] = ident_any if isinstance(ident_any, dict) else {}
        attrs_any = ident_dict.get("attrs")
        attrs_dict: dict[str, Any] = attrs_any if isinstance(attrs_any, dict) else {}
        tz_val = attrs_dict.get("timezone")
        return str(tz_val) if isinstance(tz_val, str) and tz_val else "UTC"
    except Exception:
        return "UTC"


def _format_until_local(until_iso: str, tzname: str) -> str:
    """Return a human-readable end date in user's timezone (e.g., 18 Sep 2025)."""
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        dt = datetime.fromisoformat(until_iso.replace("Z", "+00:00"))
        if tzname != "UTC":
            try:
                dt = dt.astimezone(ZoneInfo(tzname))
            except Exception:
                # Try a normalized variant like "Asia/Singapore"
                parts = tzname.split("/")
                norm = "/".join(p[:1].upper() + p[1:].lower() for p in parts)
                dt = dt.astimezone(ZoneInfo(norm))
        return dt.strftime("%d %b %Y")
    except Exception:
        return until_iso


def _auto_schedule_new_reminders(chat_id: int, settings: Settings) -> str:
    """Create reminders for prescriptions without schedules; return summary lines.

    Uses simple heuristics to suggest local times, converts to UTC for Scheduler,
    stores scheduleNames and scheduleTimes (UTC), and returns a user-friendly list
    of local times with timezone label.
    """
    try:
        from ...shared.infrastructure.identities import get_identity_by_telegram
        from ...shared.infrastructure.prescriptions_store import (
            list_prescriptions_page,
            set_prescription_schedule,
            set_prescription_schedule_names,
        )
        from ...shared.infrastructure.schedule_suggester import suggest_times_from_text
        from ...shared.infrastructure.scheduler import ReminderScheduler

        # Determine user timezone
        ident_any = get_identity_by_telegram(int(chat_id))
        ident_dict: dict[str, Any] = ident_any if isinstance(ident_any, dict) else {}
        attrs_any = ident_dict.get("attrs")
        attrs_dict: dict[str, Any] = attrs_any if isinstance(attrs_any, dict) else {}
        tz_val = attrs_dict.get("timezone")
        tzname = str(tz_val) if isinstance(tz_val, str) and tz_val else "UTC"

        # List current prescriptions
        items_tuple = list_prescriptions_page(int(chat_id), status="active", limit=50)
        items = items_tuple[0] if isinstance(items_tuple, tuple) else []

        created_lines: list[str] = []
        sched = ReminderScheduler(settings.aws_region)
        for it in items:
            if not isinstance(it, dict):
                continue
            # Skip if already scheduled
            if isinstance(it.get("scheduleTimes"), list):
                continue
            med_name = it.get("medicationName")
            freq_text = it.get("frequencyText") or it.get("dosageText")
            times_local, _reason = suggest_times_from_text(
                str(freq_text) if isinstance(freq_text, str) else None
            )
            if not times_local:
                continue
            sk_val = it.get("sk")
            if not isinstance(sk_val, str):
                continue
            # Save schedule (UTC for scheduler; local for display)
            from datetime import UTC, datetime, timedelta

            until_iso = (datetime.now(UTC) + timedelta(days=30)).isoformat()
            times_utc = (
                sched.local_times_to_utc(times_local, tzname)
                if tzname != "UTC"
                else times_local
            )
            set_prescription_schedule(int(chat_id), sk_val, times_utc, until_iso)
            names = sched.create_cron_schedules(
                int(chat_id), sk_val, times_utc, until_iso
            )
            set_prescription_schedule_names(int(chat_id), sk_val, names)
            created_lines.append(
                f"- {med_name}: {', '.join(times_local)} ({tzname}), until "
                f"{_format_until_local(until_iso, tzname)}"
            )
        return "\n".join(created_lines) if created_lines else "(no new reminders)"
    except Exception:
        _log = get_logger(__name__)
        _log.exception("auto_schedule_error")
        return "(failed to set up reminders)"


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
        # Handle location share for timezone detection
        loc = message.get("location")
        if isinstance(loc, dict):
            lat = loc.get("latitude")
            lon = loc.get("longitude")
            from_user = message.get("from") or {}
            uid2 = from_user.get("id") if isinstance(from_user, dict) else None
            if (
                isinstance(uid2, int)
                and isinstance(lat, int | float)
                and isinstance(lon, int | float)
            ):
                try:
                    from ...shared.infrastructure.identities import (
                        upsert_timezone_for_telegram,
                    )
                    from ...shared.infrastructure.timezone_infer import (
                        infer_timezone_from_coords,
                    )

                    tz = infer_timezone_from_coords(float(lat), float(lon))
                    if tz:
                        upsert_timezone_for_telegram(uid2, tz)
                        if isinstance(chat_id, int):
                            _send_message(
                                chat_id,
                                (
                                    f"Timezone set to {tz}. We'll schedule reminders "
                                    "in your local time."
                                ),
                                settings,
                                reply_markup={"remove_keyboard": True},
                            )
                except Exception:
                    logger.exception("timezone_from_location_error")

    # Enforce timezone setup before most actions
    try:
        guard_chat_id = int(chat_id) if isinstance(chat_id, int) else None
    except Exception:
        guard_chat_id = None
    # Allow-only list of actions that can proceed without a timezone
    allow_wo_tz: set[str] = {"/start", "/help", "/timezone", "/language"}
    # Extract user text (for commands) early
    text_any = message.get("text") if isinstance(message, dict) else None
    text_lower = str(text_any).strip().lower() if isinstance(text_any, str) else ""
    # If timezone missing, block unless in allow list or timezone buttons
    if isinstance(guard_chat_id, int):
        tz_now = _tz_label(guard_chat_id)
        is_tz_missing = tz_now == "UTC"
        is_timezone_flow = (
            text_lower.startswith("/timezone") or text_lower == "set timezone"
        )
        if is_tz_missing and not is_timezone_flow and text_lower not in allow_wo_tz:
            _send_message(
                guard_chat_id,
                (
                    "Please set your timezone first so I can schedule reminders "
                    "correctly. Tap ‘Set my timezone’ below or send /timezone "
                    "Asia/Singapore."
                ),
                settings,
                reply_markup={
                    "inline_keyboard": [
                        [
                            {
                                "text": "🌍 Set my timezone",
                                "callback_data": "set_timezone",
                            }
                        ]
                    ]
                },
            )
            return {"statusCode": 200, "body": "ok"}

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
                    )
                elif data == "set_language":
                    _send_message(
                        cb_chat_id,
                        (
                            "Select your preferred language for replies (medicine "
                            "names remain in English):"
                        ),
                        settings,
                        reply_markup={
                            "inline_keyboard": [
                                [
                                    {"text": "English", "callback_data": "lang_en"},
                                    {
                                        "text": "Bahasa Indonesia",
                                        "callback_data": "lang_id",
                                    },
                                ],
                                [
                                    {"text": "Malay", "callback_data": "lang_ms"},
                                    {"text": "Thai", "callback_data": "lang_th"},
                                ],
                                [
                                    {"text": "Vietnamese", "callback_data": "lang_vi"},
                                    {"text": "Tagalog", "callback_data": "lang_tl"},
                                ],
                            ]
                        },
                    )
                elif isinstance(data, str) and data.startswith("lang_"):
                    lang = data.split("_", 1)[1]
                    try:
                        upsert_language_for_telegram(int(cb_chat_id), lang)
                        _send_message(
                            cb_chat_id,
                            f"Language saved: {lang}.",
                            settings,
                        )
                    except Exception:
                        logger.exception("set_language_error")
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
                elif data == "set_timezone":
                    # Offer auto-detect (location) or quick-pick list
                    _send_message(
                        cb_chat_id,
                        (
                            "Share your location to auto-detect timezone, or pick "
                            "one below."
                        ),
                        settings,
                        reply_markup={
                            "keyboard": [
                                [
                                    {
                                        "text": "📍 Share my location",
                                        "request_location": True,
                                    }
                                ],
                                [
                                    {"text": "Asia/Singapore"},
                                    {"text": "Asia/Kuala_Lumpur"},
                                ],
                                [
                                    {"text": "Asia/Jakarta"},
                                    {"text": "Asia/Bangkok"},
                                ],
                                [
                                    {"text": "Asia/Manila"},
                                    {"text": "Asia/Ho_Chi_Minh"},
                                ],
                            ],
                            "resize_keyboard": True,
                            "one_time_keyboard": True,
                        },
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
                        # Auto-schedule for samples too
                        created_msg = _auto_schedule_new_reminders(cb_chat_id, settings)
                        _send_message(
                            cb_chat_id,
                            (
                                "Sample FHIR saved. I have set up reminders in "
                                + _tz_label(cb_chat_id)
                                + ":\n"
                                + created_msg
                                + (
                                    "\nUse /reminders to view or cancel, or send "
                                    "new times to update."
                                )
                            ),
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
                            page_lines_hist = [
                                (
                                    f"- {it.get('medicationName')}: "
                                    f"{it.get('dosageText') or ''}"
                                )
                                for it in items
                            ]
                            page_rows_hist: list[list[dict[str, str]]] = []
                            for it2 in items:
                                nm2 = str(it2.get("medicationName"))
                                sk2 = it2.get("sk")
                                if isinstance(sk2, str):
                                    page_rows_hist.append(
                                        [
                                            {
                                                "text": f"⏰ Remind: {nm2}",
                                                "callback_data": f"rx_remind::{sk2}",
                                            },
                                            {
                                                "text": f"⏹ Stop: {nm2}",
                                                "callback_data": f"rx_stop::{sk2}",
                                            },
                                        ]
                                    )
                            if next_lek:
                                page_rows_hist.append(
                                    [
                                        {
                                            "text": "Next ▶",
                                            "callback_data": "rx_history_next",
                                        }
                                    ]
                                )
                            _send_message(
                                cb_chat_id,
                                "Your prescriptions (more):\n"
                                + "\n".join(page_lines_hist),
                                settings,
                                reply_markup={"inline_keyboard": page_rows_hist}
                                if page_rows_hist
                                else {},
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
                            page_lines_active = [
                                (
                                    f"- {it.get('medicationName')}: "
                                    f"{it.get('dosageText') or ''}"
                                )
                                for it in items
                            ]
                            page_rows_active: list[list[dict[str, str]]] = []
                            for it2 in items:
                                nm2 = str(it2.get("medicationName"))
                                sk2 = it2.get("sk")
                                if isinstance(sk2, str):
                                    page_rows_active.append(
                                        [
                                            {
                                                "text": f"⏰ Remind: {nm2}",
                                                "callback_data": f"rx_remind::{sk2}",
                                            },
                                            {
                                                "text": f"⏹ Stop: {nm2}",
                                                "callback_data": f"rx_stop::{sk2}",
                                            },
                                        ]
                                    )
                            if next_lek:
                                page_rows_active.append(
                                    [
                                        {
                                            "text": "Next ▶",
                                            "callback_data": "rx_active_next",
                                        }
                                    ]
                                )
                            _send_message(
                                cb_chat_id,
                                "Active prescriptions (more):\n"
                                + "\n".join(page_lines_active),
                                settings,
                                reply_markup={"inline_keyboard": page_rows_active}
                                if page_rows_active
                                else {},
                            )
                        except Exception:
                            logger.exception("active_next_error")
                elif isinstance(data, str) and data.startswith("rx_remind_ok::"):
                    # User accepted suggested times; create schedules
                    try:
                        _, sk, label = data.split("::", 2)
                        times_raw = [t.strip() for t in label.split(",") if t.strip()]
                        from datetime import UTC, datetime, timedelta

                        from ...shared.infrastructure.identities import (
                            get_identity_by_telegram,
                        )
                        from ...shared.infrastructure.prescriptions_store import (
                            set_prescription_schedule,
                            set_prescription_schedule_names,
                        )
                        from ...shared.infrastructure.scheduler import (
                            ReminderScheduler,
                        )

                        until = (datetime.now(UTC) + timedelta(days=30)).isoformat()
                        ident = get_identity_by_telegram(cb_chat_id) or {}
                        tz = (
                            (ident.get("attrs") or {}).get("timezone")
                            if isinstance(ident, dict)
                            else None
                        )
                        tzname = str(tz) if isinstance(tz, str) and tz else "UTC"
                        times_utc = (
                            (ReminderScheduler.local_times_to_utc(times_raw, tzname))
                            if tzname != "UTC"
                            else times_raw
                        )
                        set_prescription_schedule(cb_chat_id, sk, times_raw, until)
                        sched = ReminderScheduler(settings.aws_region)
                        names = sched.create_cron_schedules(
                            cb_chat_id, sk, times_utc, until
                        )
                        set_prescription_schedule_names(cb_chat_id, sk, names)
                        # Convert to local for display
                        disp_local = (
                            ReminderScheduler.utc_times_to_local(times_utc, tzname)
                            if tzname != "UTC"
                            else times_raw
                        )
                        _send_message(
                            cb_chat_id,
                            (
                                "Reminders set at "
                                + ", ".join(disp_local)
                                + (f" ({tzname})" if tzname != "UTC" else " UTC")
                                + ". Update with /reminders or send new times."
                            ),
                            settings,
                        )
                    except Exception:
                        logger.exception("rx_remind_ok_error")
                elif isinstance(data, str) and data.startswith("rx_remind::"):
                    sk = data.split("::", 1)[1]
                    try:
                        from ...shared.infrastructure.prescriptions_store import (
                            get_prescription,
                        )
                        from ...shared.infrastructure.schedule_suggester import (
                            suggest_times_from_text,
                        )

                        rx = get_prescription(cb_chat_id, sk)
                        if not isinstance(rx, dict):
                            _send_message(cb_chat_id, "Not found.", settings)
                        else:
                            freq_text = rx.get("frequencyText") or rx.get("dosageText")
                            times, reason = suggest_times_from_text(
                                str(freq_text) if isinstance(freq_text, str) else None
                            )
                            label = ", ".join(times)
                            _send_message(
                                cb_chat_id,
                                (
                                    "Suggested reminder times (UTC): "
                                    f"{label} ({reason}).\n"
                                    "Reply with times like 08:00, 20:00 or tap OK."
                                ),
                                settings,
                                reply_markup={
                                    "inline_keyboard": [
                                        [
                                            {
                                                "text": "OK",
                                                "callback_data": (
                                                    f"rx_remind_ok::{sk}::{label}"
                                                ),
                                            }
                                        ]
                                    ]
                                },
                            )
                            st_pending = get_state(cb_chat_id)
                            st_pending["rx_remind_pending"] = {
                                "sk": sk,
                                "times": times,
                            }
                            set_state(cb_chat_id, st_pending)
                    except Exception:
                        logger.exception("rx_remind_error")
                elif isinstance(data, str) and data.startswith("rx_cancel::"):
                    # Cancel reminders for a prescription, keep RX active
                    sk = data.split("::", 1)[1]
                    try:
                        from ...shared.infrastructure.prescriptions_store import (
                            clear_prescription_schedule,
                            get_prescription,
                        )
                        from ...shared.infrastructure.scheduler import ReminderScheduler

                        rx_obj = get_prescription(cb_chat_id, sk)
                        schedule_names_raw = (
                            rx_obj.get("scheduleNames")
                            if isinstance(rx_obj, dict)
                            else None
                        )
                        schedule_names: list[str] = (
                            [str(n) for n in schedule_names_raw]
                            if isinstance(schedule_names_raw, list)
                            else []
                        )
                        if schedule_names:
                            ReminderScheduler(settings.aws_region).delete_schedules(
                                schedule_names
                            )
                        clear_prescription_schedule(cb_chat_id, sk)
                        _send_message(cb_chat_id, "Reminders cancelled.", settings)
                    except Exception:
                        logger.exception("rx_cancel_error")
                elif isinstance(data, str) and data.startswith("rx_stop::"):
                    # Stop a prescription by sk, then refresh first page of active RXs
                    sk = data.split("::", 1)[1]
                    try:
                        from ...shared.infrastructure.prescriptions_store import (
                            clear_prescription_schedule,
                            get_prescription,
                            list_prescriptions_page,
                            update_prescription_status,
                        )
                        from ...shared.infrastructure.scheduler import ReminderScheduler

                        update_prescription_status(cb_chat_id, sk, "stopped")
                        # If schedules exist, delete them
                        rx_obj2 = get_prescription(cb_chat_id, sk)
                        schedule_names_raw2 = (
                            rx_obj2.get("scheduleNames")
                            if isinstance(rx_obj2, dict)
                            else None
                        )
                        schedule_names2: list[str] = (
                            [str(n) for n in schedule_names_raw2]
                            if isinstance(schedule_names_raw2, list)
                            else []
                        )
                        if schedule_names2:
                            ReminderScheduler(settings.aws_region).delete_schedules(
                                schedule_names2
                            )
                            clear_prescription_schedule(cb_chat_id, sk)
                        # Refresh view: send one message per item with actions
                        items, lek = list_prescriptions_page(
                            cb_chat_id, status="active", limit=5
                        )
                        if not items:
                            _send_message(
                                cb_chat_id, "No active prescriptions.", settings
                            )
                        else:
                            for it in items[:5]:
                                name_txt = str(it.get("medicationName"))
                                dose_txt = str(it.get("dosageText") or "")
                                sk_val = it.get("sk")
                                kb = {}
                                if isinstance(sk_val, str):
                                    kb = {
                                        "inline_keyboard": [
                                            [
                                                {
                                                    "text": (f"⏰ Remind: {name_txt}"),
                                                    "callback_data": (
                                                        f"rx_remind::{sk_val}"
                                                    ),
                                                },
                                                {
                                                    "text": (f"⏹ Stop: {name_txt}"),
                                                    "callback_data": (
                                                        f"rx_stop::{sk_val}"
                                                    ),
                                                },
                                            ]
                                        ]
                                    }
                                _send_message(
                                    cb_chat_id,
                                    f"- {name_txt}: {dose_txt}",
                                    settings,
                                    reply_markup=kb,
                                )
                            if lek:
                                _send_message(
                                    cb_chat_id,
                                    "More items available…",
                                    settings,
                                    reply_markup={
                                        "inline_keyboard": [
                                            [
                                                {
                                                    "text": "Next ▶",
                                                    "callback_data": "rx_active_next",
                                                }
                                            ]
                                        ]
                                    },
                                )
                    except Exception:
                        logger.exception("rx_stop_error")
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
                            [
                                {
                                    "text": "🌍 Set my timezone",
                                    "callback_data": "set_timezone",
                                }
                            ],
                            [
                                {
                                    "text": "🌐 Set language",
                                    "callback_data": "set_language",
                                }
                            ],
                        ]
                    },
                )
                # If identity lacks phone, ask for contact share
                try:
                    from_user = message.get("from") or {}
                    uid_start = (
                        from_user.get("id") if isinstance(from_user, dict) else None
                    )
                    if isinstance(uid_start, int):
                        ident_start = get_identity_by_telegram(uid_start) or {}
                        phone_start = (
                            ident_start.get("phone")
                            if isinstance(ident_start, dict)
                            else None
                        )
                        if not phone_start:
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
                        "- Set up reminders and adherence schedules.\n"
                        "- Set your timezone (auto-detect via location or quick-pick)"
                        " for local-time reminders.\n\n"
                        "Change reminder times:\n"
                        "1) Open /active or /history and tap ⏰ Remind under a "
                        "prescription.\n"
                        "2) Reply with times in 24h HH:MM, comma-separated (e.g., "
                        "08:00, 19:00), or tap OK to accept suggestions.\n"
                        "3) To clear and reset: go to /reminders and tap ❌ Cancel for"
                        " that item, then set new times via ⏰ Remind.\n\n"
                        "Language:\n"
                        "- Set your preferred language for replies. Medicine names "
                        "stay in English.\n\n"
                        "Commands:\n"
                        "/start — show the main menu\n"
                        "/help — this help\n"
                        "/history — recent prescriptions\n"
                        "/active — active prescriptions\n"
                        "/reminders — show reminder schedules\n"
                        "/timezone [IANA_TZ] — set timezone (e.g., /timezone "
                        "Asia/Singapore)\n\n"
                        "/language [code] — set language (e.g., /language id). "
                        "No code shows a picker.\n\n"
                        'Tip: You can also ask, e.g. "what are my active '
                        'prescriptions?"'
                    ),
                    settings,
                )
                return {"statusCode": 200, "body": "ok"}
            if cmd == "timezone":
                # /timezone [IANA_TZ]
                tz_arg = (_args or "").strip() if isinstance(_args, str) else ""
                if tz_arg:
                    try:
                        from ...shared.infrastructure.identities import (
                            upsert_timezone_for_telegram,
                        )

                        from_user = message.get("from") or {}
                        uid = (
                            from_user.get("id") if isinstance(from_user, dict) else None
                        )
                        if isinstance(uid, int):
                            upsert_timezone_for_telegram(uid, tz_arg)
                            _send_message(
                                chat_id,
                                f"Timezone set to {tz_arg}.",
                                settings,
                                reply_markup={"remove_keyboard": True},
                            )
                    except Exception:
                        logger.exception("timezone_cmd_error")
                else:
                    _send_message(
                        chat_id,
                        (
                            "Share your location to auto-detect timezone, or pick "
                            "one below, or reply with an IANA name (e.g., "
                            "Asia/Singapore)."
                        ),
                        settings,
                        reply_markup={
                            "keyboard": [
                                [
                                    {
                                        "text": "📍 Share my location",
                                        "request_location": True,
                                    }
                                ],
                                [
                                    {"text": "Asia/Singapore"},
                                    {"text": "Asia/Kuala_Lumpur"},
                                ],
                                [
                                    {"text": "Asia/Jakarta"},
                                    {"text": "Asia/Bangkok"},
                                ],
                                [
                                    {"text": "Asia/Manila"},
                                    {"text": "Asia/Ho_Chi_Minh"},
                                ],
                            ],
                            "resize_keyboard": True,
                            "one_time_keyboard": True,
                        },
                    )
                return {"statusCode": 200, "body": "ok"}
            if cmd == "language":
                # /language [code]
                lang_arg = (_args or "").strip() if isinstance(_args, str) else ""
                if lang_arg:
                    try:
                        from_user = message.get("from") or {}
                        uid = (
                            from_user.get("id") if isinstance(from_user, dict) else None
                        )
                        if isinstance(uid, int):
                            upsert_language_for_telegram(uid, lang_arg)
                            _send_message(
                                chat_id,
                                f"Language saved: {lang_arg}.",
                                settings,
                            )
                    except Exception:
                        logger.exception("language_cmd_error")
                else:
                    _send_message(
                        chat_id,
                        (
                            "Select your preferred language for replies "
                            "(medicine names remain in English):"
                        ),
                        settings,
                        reply_markup={
                            "inline_keyboard": [
                                [
                                    {"text": "English", "callback_data": "lang_en"},
                                    {
                                        "text": "Bahasa Indonesia",
                                        "callback_data": "lang_id",
                                    },
                                ],
                                [
                                    {"text": "Malay", "callback_data": "lang_ms"},
                                    {"text": "Thai", "callback_data": "lang_th"},
                                ],
                                [
                                    {"text": "Vietnamese", "callback_data": "lang_vi"},
                                    {"text": "Tagalog", "callback_data": "lang_tl"},
                                ],
                            ]
                        },
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
                    # Per-item action rows
                    kb_rows: list[list[dict[str, str]]] = []
                    history_item_lines: list[str] = []
                    for it in items[:5]:
                        name = it.get("medicationName")
                        dose = it.get("dosageText") or ""
                        history_item_lines.append(f"- {name}: {dose}")
                        sk_val = it.get("sk")
                        if isinstance(sk_val, str):
                            kb_rows.append(
                                [
                                    {
                                        "text": "⏰ Remind",
                                        "callback_data": f"rx_remind::{sk_val}",
                                    },
                                    {
                                        "text": "⏹ Stop",
                                        "callback_data": f"rx_stop::{sk_val}",
                                    },
                                ]
                            )
                    if st.get("rx_history_lek"):
                        kb_rows.append(
                            [
                                {
                                    "text": "Next ▶",
                                    "callback_data": "rx_history_next",
                                }
                            ]
                        )
                    _send_message(
                        chat_id,
                        "Your prescriptions:\n" + "\n".join(history_item_lines),
                        settings,
                        reply_markup={"inline_keyboard": kb_rows} if kb_rows else {},
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
                    st_active = get_state(chat_id)
                    st_active["rx_active_lek"] = lek
                    set_state(chat_id, st_active)
                except Exception:
                    logger.exception("active_list_error")
                if not items:
                    _send_message(chat_id, "No active prescriptions.", settings)
                else:
                    # Send one message per item so buttons appear under each line
                    for it in items[:5]:
                        name_txt = str(it.get("medicationName"))
                        dose_txt = str(it.get("dosageText") or "")
                        sk_val = it.get("sk")
                        kb = {}
                        if isinstance(sk_val, str):
                            kb = {
                                "inline_keyboard": [
                                    [
                                        {
                                            "text": f"⏰ Remind: {name_txt}",
                                            "callback_data": f"rx_remind::{sk_val}",
                                        },
                                        {
                                            "text": f"⏹ Stop: {name_txt}",
                                            "callback_data": f"rx_stop::{sk_val}",
                                        },
                                    ]
                                ]
                            }
                        _send_message(
                            chat_id,
                            f"- {name_txt}: {dose_txt}",
                            settings,
                            reply_markup=kb,
                        )
                    if st_active.get("rx_active_lek"):
                        _send_message(
                            chat_id,
                            "More items available…",
                            settings,
                            reply_markup={
                                "inline_keyboard": [
                                    [
                                        {
                                            "text": "Next ▶",
                                            "callback_data": "rx_active_next",
                                        }
                                    ]
                                ]
                            },
                        )
                return {"statusCode": 200, "body": "ok"}
            if cmd == "reminders":
                # List current schedules (from materialized RX items), per-item
                try:
                    from ...shared.infrastructure.prescriptions_store import (
                        list_prescriptions_page,
                    )
                    from ...shared.infrastructure.scheduler import ReminderScheduler

                    items_tuple = list_prescriptions_page(
                        int(chat_id) if isinstance(chat_id, int) else 0,
                        limit=50,
                    )
                    items = items_tuple[0] if isinstance(items_tuple, tuple) else []
                    tz_list_label = _tz_label(
                        int(chat_id) if isinstance(chat_id, int) else 0
                    )
                    any_sent = False
                    for it in items:
                        nm_any = it.get("medicationName")
                        nm = str(nm_any) if nm_any is not None else "(unknown)"
                        times_any = it.get("scheduleTimes")
                        until_any = it.get("scheduleUntil")
                        sk_val = it.get("sk")
                        if isinstance(times_any, list) and times_any:
                            times_strs = [str(x) for x in times_any]
                            times_local = (
                                ReminderScheduler.utc_times_to_local(
                                    times_strs, tz_list_label
                                )
                                if tz_list_label != "UTC"
                                else times_strs
                            )
                            label = ", ".join(times_local)
                            until_h = _format_until_local(str(until_any), tz_list_label)
                            kb = {}
                            if isinstance(sk_val, str):
                                kb = {
                                    "inline_keyboard": [
                                        [
                                            {
                                                "text": "❌ Cancel reminders",
                                                "callback_data": f"rx_cancel::{sk_val}",
                                            }
                                        ]
                                    ]
                                }
                            _send_message(
                                chat_id,
                                f"- {nm}: {label} ({tz_list_label}), until {until_h}",
                                settings,
                                reply_markup=kb,
                            )
                            any_sent = True
                    if not any_sent:
                        _send_message(chat_id, "No active reminders.", settings)
                except Exception:
                    logger.exception("reminders_list_error")
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
            elif state.get("rx_remind_pending") and has_text:
                # User provided custom times, e.g. "08:00, 20:00"
                try:
                    from ...shared.infrastructure.identities import (
                        get_identity_by_telegram,
                    )
                    from ...shared.infrastructure.prescriptions_store import (
                        set_prescription_schedule,
                    )
                    from ...shared.infrastructure.schedule_suggester import (
                        parse_times_user_input,
                    )
                    from ...shared.infrastructure.scheduler import ReminderScheduler

                    pending_any = state.get("rx_remind_pending")
                    pending: dict[str, Any] = (
                        pending_any if isinstance(pending_any, dict) else {}
                    )
                    sk_any = pending.get("sk")
                    sk_pending: str | None = sk_any if isinstance(sk_any, str) else None
                    times_list_custom = parse_times_user_input(
                        str(message.get("text", ""))
                    )
                    times_custom: list[str] = (
                        times_list_custom if isinstance(times_list_custom, list) else []
                    )
                    if not (
                        isinstance(sk_pending, str)
                        and isinstance(times_custom, list)
                        and times_custom
                    ):
                        _send_message(
                            chat_id,
                            "Please provide times like 08:00, 20:00",
                            settings,
                        )
                    else:
                        # Default 30 days if no stock info yet
                        from datetime import UTC, datetime, timedelta

                        until = (datetime.now(UTC) + timedelta(days=30)).isoformat()
                        ident_any = get_identity_by_telegram(int(chat_id))
                        ident_dict: dict[str, Any] = (
                            ident_any if isinstance(ident_any, dict) else {}
                        )
                        attrs_any = ident_dict.get("attrs")
                        attrs_dict: dict[str, Any] = (
                            attrs_any if isinstance(attrs_any, dict) else {}
                        )
                        tz_val_any = attrs_dict.get("timezone")
                        tzname = (
                            str(tz_val_any)
                            if isinstance(tz_val_any, str) and tz_val_any
                            else "UTC"
                        )
                        times_utc = (
                            ReminderScheduler.local_times_to_utc(times_custom, tzname)
                            if tzname != "UTC"
                            else list(times_custom)
                        )
                        set_prescription_schedule(
                            int(chat_id), sk_pending, times_custom, until
                        )
                        ReminderScheduler(settings.aws_region).create_cron_schedules(
                            int(chat_id), sk_pending, times_utc, until
                        )
                        disp_local2 = (
                            ReminderScheduler.utc_times_to_local(times_utc, tzname)
                            if tzname != "UTC"
                            else list(times_custom)
                        )
                        _send_message(
                            chat_id,
                            (
                                "Reminders set at "
                                + ", ".join(disp_local2)
                                + (f" ({tzname})" if tzname != "UTC" else " UTC")
                                + ". You can update anytime by sending new times."
                            ),
                            settings,
                        )
                        after3 = get_state(chat_id)
                        after3.pop("rx_remind_pending", None)
                        set_state(chat_id, after3)
                except Exception:
                    logger.exception("rx_remind_custom_error")
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
                    # Handle quick-pick timezone text
                    if text_lower in {
                        "asia/singapore",
                        "asia/kuala_lumpur",
                        "asia/jakarta",
                        "asia/bangkok",
                        "asia/manila",
                        "asia/ho_chi_minh",
                    }:
                        try:
                            from ...shared.infrastructure.identities import (
                                upsert_timezone_for_telegram,
                            )

                            from_user = message.get("from") or {}
                            uid = (
                                from_user.get("id")
                                if isinstance(from_user, dict)
                                else None
                            )
                            if isinstance(uid, int):
                                upsert_timezone_for_telegram(uid, text_lower)
                                _send_message(
                                    chat_id,
                                    f"Timezone set to {text_lower}.",
                                    settings,
                                    reply_markup={"remove_keyboard": True},
                                )
                                return {"statusCode": 200, "body": "ok"}
                        except Exception:
                            logger.exception("timezone_quickpick_error")
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
                                rows: list[list[dict[str, str]]] = []
                                for it in items[:5]:
                                    sk_val = it.get("sk")
                                    if isinstance(sk_val, str):
                                        rows.append(
                                            [
                                                {
                                                    "text": "⏹ Stop",
                                                    "callback_data": (
                                                        f"rx_stop::{sk_val}"
                                                    ),
                                                }
                                            ]
                                        )
                                reply_markup = {"inline_keyboard": rows} if rows else {}
                                _send_message(
                                    chat_id,
                                    "Active prescriptions:\n" + "\n".join(lines),
                                    settings,
                                    reply_markup=reply_markup,
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
