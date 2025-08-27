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

    def save_bundle(self, user_id: int, bundle: dict[str, Any]) -> str:
        if self._table is None:
            raise RuntimeError("FHIR_TABLE_NAME not configured")
        ts = datetime.now(UTC).isoformat()
        sk = f"FHIR#BUNDLE#{ts}"
        self._table.put_item(
            Item={
                "pk": f"USER#{user_id}",
                "sk": sk,
                "bundle": bundle,
                "createdAt": ts,
            }
        )
        return sk
