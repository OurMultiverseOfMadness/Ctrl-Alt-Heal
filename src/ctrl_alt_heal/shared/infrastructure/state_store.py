from __future__ import annotations

import os
from typing import Any

import boto3

_dynamodb = boto3.resource("dynamodb")
_table_name = os.environ.get("TABLE_NAME", "")
_table = _dynamodb.Table(_table_name) if _table_name else None


def _ensure_table() -> None:
    if _table is None:
        raise RuntimeError("TABLE_NAME not configured for state store")


def get_state(chat_id: int) -> dict[str, Any]:
    _ensure_table()
    resp = _table.get_item(Key={"pk": f"CHAT#{chat_id}", "sk": "STATE"})  # type: ignore[union-attr]
    return resp.get("Item", {}).get("data", {}) if resp.get("Item") else {}


def set_state(chat_id: int, data: dict[str, Any]) -> None:
    _ensure_table()
    _table.put_item(  # type: ignore[union-attr]
        Item={
            "pk": f"CHAT#{chat_id}",
            "sk": "STATE",
            "data": data,
        }
    )


def clear_state(chat_id: int) -> None:
    _ensure_table()
    _table.delete_item(  # type: ignore[union-attr]
        Key={"pk": f"CHAT#{chat_id}", "sk": "STATE"}
    )
