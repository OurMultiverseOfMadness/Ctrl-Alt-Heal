from __future__ import annotations

import os
from typing import Any

import boto3

_ddb = boto3.resource("dynamodb")
_table_name = os.environ.get("USER_TABLE_NAME", "")
_table = _ddb.Table(_table_name) if _table_name else None


def _ensure_table() -> None:
    if _table is None:
        raise RuntimeError("USER_TABLE_NAME not configured")


def link_telegram_user(
    telegram_user_id: int, phone: str | None, attrs: dict[str, Any] | None = None
) -> None:
    _ensure_table()
    item = {
        "pk": f"TG#{telegram_user_id}",
        "sk": "IDENTITY",
        "phone": phone,
        "attrs": attrs or {},
    }
    _table.put_item(Item=item)  # type: ignore[union-attr]


def get_identity_by_telegram(telegram_user_id: int) -> dict[str, Any] | None:
    _ensure_table()
    resp = _table.get_item(Key={"pk": f"TG#{telegram_user_id}", "sk": "IDENTITY"})  # type: ignore[union-attr]
    return resp.get("Item") if resp.get("Item") else None
