from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from typing import Any

import boto3


class FhirStore:
    """A class for interacting with the FHIR DynamoDB table."""

    def __init__(self, table_name: str | None = None) -> None:
        self._table_name = table_name or os.getenv("FHIR_DATA_TABLE_NAME") or ""
        self._ddb = boto3.resource("dynamodb")
        self._table = self._ddb.Table(self._table_name) if self._table_name else None

    def _ensure_table(self) -> None:
        if self._table is None:
            raise RuntimeError("FHIR_DATA_TABLE_NAME not configured")

    def save_bundle(self, user_id: str, bundle: dict[str, Any]) -> str:
        """Saves a FHIR bundle to the database."""
        self._ensure_table()
        assert self._table is not None
        ts = datetime.now(UTC).isoformat()
        resource_id = f"BUNDLE#{uuid.uuid4()}"
        self._table.put_item(
            Item={
                "user_id": user_id,
                "resource_id": resource_id,
                "bundle": bundle,
                "createdAt": ts,
                "updatedAt": ts,
            }
        )
        return resource_id
