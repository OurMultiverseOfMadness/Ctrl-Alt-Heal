from __future__ import annotations

import os
from datetime import UTC, datetime

import boto3
from botocore.exceptions import ClientError

from ctrl_alt_heal.domain.models import Identity


class IdentitiesStore:
    def __init__(self, table_name: str | None = None) -> None:
        self.table_name = table_name or os.getenv("IDENTITIES_TABLE_NAME")
        if not self.table_name:
            raise ValueError("IDENTITIES_TABLE_NAME environment variable not set.")
        self.ddb = boto3.resource("dynamodb")
        self.table = self.ddb.Table(self.table_name)

    def find_user_id_by_identity(
        self, provider: str, provider_user_id: str
    ) -> str | None:
        """Finds an internal user_id based on an external identity."""
        try:
            composite_key = f"{provider}#{provider_user_id}"
            response = self.table.get_item(Key={"identity_key": composite_key})
            if "Item" in response:
                return response["Item"]["user_id"]
            return None
        except ClientError as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error finding user by identity: {e}")
            return None

    def link_identity(self, identity: Identity) -> None:
        """Creates a new identity link in DynamoDB."""
        identity.created_at = datetime.now(UTC).isoformat()
        if not identity.pk:
            identity.pk = f"{identity.provider}#{identity.provider_user_id}"

        # Convert the Identity model to a dict and use the correct key name
        item = identity.model_dump()
        # Replace 'pk' with 'identity_key' to match the table schema
        if "pk" in item:
            item["identity_key"] = item.pop("pk")

        self.table.put_item(Item=item)
