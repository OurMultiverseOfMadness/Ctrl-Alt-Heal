from __future__ import annotations

import json
from typing import Any


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # EventBridge Scheduler target stub.
    # Expecting an event payload with patient_id, regimen_id, dose_id, and message.
    # In production: fetch regimen/dose from DB, ensure idempotency,
    # send Telegram message, and mark completion state.
    try:
        body = event if isinstance(event, dict) else {}
        _ = body.get("patient_id"), body.get("regimen_id"), body.get("dose_id")
    except Exception:
        return {"statusCode": 400, "body": "invalid event"}

    return {"statusCode": 200, "body": json.dumps({"status": "sent"})}
