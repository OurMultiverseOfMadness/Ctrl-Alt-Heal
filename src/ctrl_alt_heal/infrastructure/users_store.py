from __future__ import annotations

import os
from datetime import UTC, datetime

import boto3
from botocore.exceptions import ClientError

from ctrl_alt_heal.domain.models import User


class UsersStore:
    def __init__(self, table_name: str | None = None) -> None:
        self.table_name = table_name or os.getenv("USERS_TABLE_NAME")
        if not self.table_name:
            raise ValueError("USERS_TABLE_NAME environment variable not set.")
        self.ddb = boto3.resource("dynamodb")
        self.table = self.ddb.Table(self.table_name)

    def get_user(self, user_id: str) -> User | None:
        """Retrieves a user from DynamoDB by their internal user_id."""
        try:
            response = self.table.get_item(Key={"user_id": user_id})
            if "Item" in response:
                return User(**response["Item"])
            return None
        except ClientError as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error getting user: {e}")
            return None

    def upsert_user(self, user: User) -> None:
        """Creates or updates a user in DynamoDB."""
        user.updated_at = datetime.now(UTC).isoformat()
        self.table.put_item(Item=user.model_dump())
