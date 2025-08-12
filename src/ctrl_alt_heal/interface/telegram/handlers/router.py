from __future__ import annotations

from typing import Any


def route_update(update: dict[str, Any]) -> dict[str, Any]:
    # Minimal router: echo type back
    if "message" in update:
        return {"type": "message"}
    if "edited_message" in update:
        return {"type": "edited_message"}
    if "callback_query" in update:
        return {"type": "callback_query"}
    return {"type": "unknown"}


def parse_command(update: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (command, args) if a slash command exists, else (None, None)."""
    message = update.get("message") or update.get("edited_message") or {}
    text = message.get("text")
    if not isinstance(text, str) or not text.startswith("/"):
        return None, None
    parts = text.strip().split(maxsplit=1)
    cmd = parts[0][1:].lower()
    args = parts[1] if len(parts) > 1 else None
    return cmd, args
