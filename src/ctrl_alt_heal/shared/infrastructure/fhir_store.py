from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import boto3


class FhirStore:
    def __init__(self, table_name: str | None = None) -> None:
        self._table_name = table_name or os.getenv("FHIR_TABLE_NAME") or ""
        self._ddb = boto3.resource("dynamodb")
        self._table = self._ddb.Table(self._table_name) if self._table_name else None

    def save_bundle(self, chat_id: int, bundle: dict[str, Any]) -> None:
        if self._table is None:
            raise RuntimeError("FHIR_TABLE_NAME not configured")
        ts = datetime.now(UTC).isoformat()
        self._table.put_item(
            Item={
                "pk": f"CHAT#{chat_id}",
                "sk": f"FHIR#BUNDLE#{ts}",
                "bundle": bundle,
                "createdAt": ts,
            }
        )
