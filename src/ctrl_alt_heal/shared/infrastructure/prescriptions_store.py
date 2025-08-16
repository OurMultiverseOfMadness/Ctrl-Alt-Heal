from __future__ import annotations

import hashlib
import os
from typing import Any

import boto3

_ddb = boto3.resource("dynamodb")
_table_name = os.environ.get("PRESCRIPTIONS_TABLE_NAME", "")
_table = _ddb.Table(_table_name) if _table_name else None


def _ensure_table() -> None:
    if _table is None:
        raise RuntimeError("PRESCRIPTIONS_TABLE_NAME not configured")


def _hash_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def save_prescription(
    chat_id: int,
    name: str,
    dosage_text: str | None,
    frequency_text: str | None,
    status: str,
    source_bundle_sk: str | None,
    start_iso: str | None,
    extra: dict[str, Any] | None = None,
) -> None:
    _ensure_table()
    rx_key = _hash_id("|".join([name or "", dosage_text or "", start_iso or ""]))
    item: dict[str, Any] = {
        "pk": f"CHAT#{chat_id}",
        "sk": f"RX#{start_iso or '0000'}#{rx_key}",
        "medicationName": name,
        "dosageText": dosage_text,
        "frequencyText": frequency_text,
        "status": status,
        "sourceBundleSk": source_bundle_sk,
    }
    if extra:
        item.update({f"x_{k}": v for k, v in extra.items()})
    _table.put_item(Item=item)  # type: ignore[union-attr]


def list_prescriptions_page(
    chat_id: int,
    *,
    status: str | None = None,
    limit: int = 10,
    last_evaluated_key: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    _ensure_table()
    kwargs: dict[str, Any] = {
        "KeyConditionExpression": boto3.dynamodb.conditions.Key("pk").eq(
            f"CHAT#{chat_id}"
        ),
        "Limit": limit,
    }
    if last_evaluated_key:
        kwargs["ExclusiveStartKey"] = last_evaluated_key
    resp = _table.query(**kwargs)  # type: ignore[arg-type]
    items = resp.get("Items") or []
    if status:
        items = [it for it in items if it.get("status") == status]
    return items, resp.get("LastEvaluatedKey")


def list_prescriptions(
    chat_id: int,
    status: str | None = None,
    limit: int = 10,
    last_evaluated_key: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    items, _ = list_prescriptions_page(
        chat_id, status=status, limit=limit, last_evaluated_key=last_evaluated_key
    )
    return items


def update_prescription_status(chat_id: int, sk: str, status: str) -> None:
    _ensure_table()
    _table.update_item(  # type: ignore[union-attr]
        Key={"pk": f"CHAT#{chat_id}", "sk": sk},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status},
    )


def get_prescription(chat_id: int, sk: str) -> dict[str, Any] | None:
    _ensure_table()
    resp = _table.get_item(  # type: ignore[union-attr]
        Key={"pk": f"CHAT#{chat_id}", "sk": sk}
    )
    item = resp.get("Item") if isinstance(resp, dict) else None
    return item if isinstance(item, dict) else None
