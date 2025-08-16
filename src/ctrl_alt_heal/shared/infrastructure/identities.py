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
    """Create or update identity; do not wipe existing phone if not provided."""
    _ensure_table()
    existing = get_identity_by_telegram(telegram_user_id) or {}
    # Preserve existing phone if incoming phone is None/empty
    final_phone = phone if isinstance(phone, str) and phone else existing.get("phone")
    # Shallow-merge attrs
    merged_attrs: dict[str, Any] = {}
    if isinstance(existing.get("attrs"), dict):
        merged_attrs.update(existing.get("attrs") or {})
    if isinstance(attrs, dict):
        merged_attrs.update(attrs)
    item = {
        "pk": f"TG#{telegram_user_id}",
        "sk": "IDENTITY",
        "phone": final_phone,
        "attrs": merged_attrs,
    }
    _table.put_item(Item=item)  # type: ignore[union-attr]


def get_identity_by_telegram(telegram_user_id: int) -> dict[str, Any] | None:
    _ensure_table()
    resp = _table.get_item(Key={"pk": f"TG#{telegram_user_id}", "sk": "IDENTITY"})  # type: ignore[union-attr]
    return resp.get("Item") if resp.get("Item") else None


def upsert_phone_for_telegram(telegram_user_id: int, phone: str) -> None:
    _ensure_table()
    current = get_identity_by_telegram(telegram_user_id) or {}
    item = {
        "pk": f"TG#{telegram_user_id}",
        "sk": "IDENTITY",
        "phone": phone,
        "attrs": current.get("attrs") or {},
    }
    _table.put_item(Item=item)  # type: ignore[union-attr]


def upsert_timezone_for_telegram(telegram_user_id: int, timezone: str) -> None:
    """Store user's IANA timezone in attrs.timezone."""
    _ensure_table()
    current = get_identity_by_telegram(telegram_user_id) or {}
    attrs = current.get("attrs") or {}
    if not isinstance(attrs, dict):
        attrs = {}
    attrs["timezone"] = timezone
    item = {
        "pk": f"TG#{telegram_user_id}",
        "sk": "IDENTITY",
        "phone": current.get("phone"),
        "attrs": attrs,
    }
    _table.put_item(Item=item)  # type: ignore[union-attr]
