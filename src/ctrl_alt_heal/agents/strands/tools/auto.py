from __future__ import annotations

from typing import Any

from ....interface.telegram.handlers.router import parse_command
from ....shared.infrastructure.logger import get_logger
from .chat import chat_tool


def auto_tool(payload: dict[str, Any]) -> dict[str, Any]:
    """Auto-route updates to the appropriate tool and return a unified result.

    Input:  {"update": <telegram_update_dict>}
    Output: {"tool": str, "reply": str, ...tool-specific fields}
    """
    logger = get_logger(__name__)
    update = payload.get("update")
    if not isinstance(update, dict):
        return {"error": "missing_update"}

    message = update.get("message") or update.get("edited_message") or {}
    # File ingestion: ask the user which type for MVP
    if "document" in message or "photo" in message:
        prompt = (
            "Is this a pharmacy label (single medication) or a doctor's prescription "
            "(multiple medications)? Reply with 'label' or 'prescription'."
        )
        return {"tool": "ask_source_type", "reply": prompt}

    # Text handling
    text = message.get("text")
    if isinstance(text, str) and text.strip():
        cmd, args = parse_command(update)
        if cmd:  # simple built-in command replies
            logger.info("auto_tool_cmd", extra={"cmd": cmd})
            replies = {
                "start": (
                    "Welcome! Send a photo or PDF of your prescription to begin."
                ),
                "help": (
                    "You can send prescriptions, ask questions, and schedule reminders."
                ),
                "status": "I'll summarize your current reminders soon.",
                "cancel": "Okay, cancel which reminder?",
                "upload": "Please send the prescription file now.",
                "schedule": (
                    "Tell me what to schedule (e.g., '9am daily for 7 days')."
                ),
            }
            return {"tool": "command", "reply": replies.get(cmd, "OK.")}

        # Conversational chat via model
        out = chat_tool({"text": text})
        logger.info(
            "auto_tool_route", extra={"target": "chat", "error": out.get("error")}
        )
        return {"tool": "chat", **out}

    # Fallback
    return {"tool": "none", "reply": "OK"}
