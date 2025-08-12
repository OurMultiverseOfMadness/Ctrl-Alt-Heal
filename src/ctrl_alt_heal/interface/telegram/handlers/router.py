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
