from __future__ import annotations

import os

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from ctrl_alt_heal.domain.models import ConversationHistory


class HistoryStore:
    def __init__(self, table_name: str | None = None) -> None:
        """Initializes the HistoryStore."""
        self.table_name = table_name or os.getenv("CONVERSATIONS_TABLE_NAME")
        if not self.table_name:
            raise ValueError("CONVERSATIONS_TABLE_NAME environment variable not set.")
        self.ddb = boto3.resource("dynamodb")
        self.table = self.ddb.Table(self.table_name)

    def save_history(self, history: ConversationHistory) -> None:
        """Saves the conversation history to DynamoDB."""
        self.table.put_item(Item=history.model_dump())

    def get_latest_history(self, user_id: str) -> ConversationHistory | None:
        """Retrieves the most recent conversation history session from DynamoDB."""
        try:
            response = self.table.query(
                KeyConditionExpression=Key("user_id").eq(user_id),
                ScanIndexForward=False,  # Sort descending to get the latest
                Limit=1,
            )
            if response.get("Items"):
                return ConversationHistory(**response["Items"][0])
        except ClientError as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Could not get history for {user_id}: {e}")
        return None
