from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime

import boto3
from typing import Any


class PrescriptionsStore:
    def __init__(self, table_name: str | None = None) -> None:
        self._table_name = table_name or os.getenv("PRESCRIPTIONS_TABLE_NAME") or ""
        self._ddb = boto3.resource("dynamodb")
        self._table = self._ddb.Table(self._table_name) if self._table_name else None

    def save_prescription(
        self,
        user_id: str,
        name: str,
        dosage_text: str,
        frequency_text: str,
        status: str,
        start_iso: str | None,
        source_bundle_sk: str | None,
    ) -> str:
        """Saves a prescription to the database."""
        if self._table is None:
            raise RuntimeError("PRESCRIPTIONS_TABLE_NAME not configured")
        ts = datetime.now(UTC).isoformat()
        sk = f"PRESCRIPTION#{uuid.uuid4()}"
        self._table.put_item(
            Item={
                "pk": f"USER#{user_id}",
                "sk": sk,
                "name": name,
                "dosageText": dosage_text,
                "frequencyText": frequency_text,
                "status": status,
                "start": start_iso,
                "sourceBundleSK": source_bundle_sk,
                "createdAt": ts,
                "updatedAt": ts,
            }
        )
        return sk

    def list_prescriptions_page(
        self,
        user_id: str,
        *,
        status: str | None = None,
        limit: int = 10,
        last_evaluated_key: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        self._ensure_table()
        assert self._table is not None
        kwargs: dict[str, Any] = {
            "KeyConditionExpression": boto3.dynamodb.conditions.Key("pk").eq(
                f"USER#{user_id}"
            ),
            "Limit": limit,
        }
        if last_evaluated_key:
            kwargs["ExclusiveStartKey"] = last_evaluated_key
        resp = self._table.query(**kwargs)
        items = resp.get("Items") or []
        if status:
            items = [it for it in items if it.get("status") == status]
        return items, resp.get("LastEvaluatedKey")

    def list_prescriptions(
        self,
        user_id: str,
        status: str | None = None,
        limit: int = 10,
        last_evaluated_key: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        items, _ = self.list_prescriptions_page(
            user_id, status=status, limit=limit, last_evaluated_key=last_evaluated_key
        )
        return items

    def update_prescription_status(self, user_id: str, sk: str, status: str) -> None:
        self._ensure_table()
        self._table.update_item(  # type: ignore[union-attr]
            Key={"pk": f"USER#{user_id}", "sk": sk},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": status},
        )

    def get_prescription(self, user_id: str, sk: str) -> dict[str, Any] | None:
        self._ensure_table()
        assert self._table is not None
        resp = self._table.get_item(Key={"pk": f"USER#{user_id}", "sk": sk})
        item = resp.get("Item") if isinstance(resp, dict) else None
        return item if isinstance(item, dict) else None

    def set_prescription_schedule(
        self, user_id: str, sk: str, times_utc_hhmm: list[str], until_iso: str
    ) -> None:
        self._ensure_table()
        self._table.update_item(  # type: ignore[union-attr]
            Key={"pk": f"USER#{user_id}", "sk": sk},
            UpdateExpression="SET #t = :t, #u = :u",
            ExpressionAttributeNames={"#t": "scheduleTimes", "#u": "scheduleUntil"},
            ExpressionAttributeValues={":t": times_utc_hhmm, ":u": until_iso},
        )

    def set_prescription_schedule_names(
        self, user_id: str, sk: str, schedule_names: list[str]
    ) -> None:
        self._ensure_table()
        self._table.update_item(  # type: ignore[union-attr]
            Key={"pk": f"USER#{user_id}", "sk": sk},
            UpdateExpression="SET #n = :n",
            ExpressionAttributeNames={"#n": "scheduleNames"},
            ExpressionAttributeValues={":n": schedule_names},
        )

    def clear_prescription_schedule(self, user_id: str, sk: str) -> None:
        self._ensure_table()
        self._table.update_item(  # type: ignore[union-attr]
            Key={"pk": f"USER#{user_id}", "sk": sk},
            UpdateExpression=("REMOVE #t, #u, #n"),
            ExpressionAttributeNames={
                "#t": "scheduleTimes",
                "#u": "scheduleUntil",
                "#n": "scheduleNames",
            },
        )
