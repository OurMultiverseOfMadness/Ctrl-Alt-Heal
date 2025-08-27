from __future__ import annotations

import os

import boto3
from botocore.exceptions import ClientError

from ctrl_alt_heal.domain.models import ConversationHistory


class HistoryStore:
    def __init__(self, table_name: str | None = None) -> None:
        """Initializes the HistoryStore."""
        self.table_name = table_name or os.getenv("HISTORY_TABLE_NAME")
        if not self.table_name:
            raise ValueError("HISTORY_TABLE_NAME environment variable not set.")
        self.ddb = boto3.resource("dynamodb")
        self.table = self.ddb.Table(self.table_name)

    def save_history(self, history: ConversationHistory) -> None:
        """Saves the conversation history to DynamoDB."""
        self.table.put_item(Item=history.model_dump())

    def get_history(self, user_id: str) -> ConversationHistory:
        """Retrieves the conversation history from DynamoDB."""
        try:
            response = self.table.get_item(Key={"user_id": user_id})
            if "Item" in response:
                return ConversationHistory(**response["Item"])
        except ClientError as e:
            print(f"Could not get history for {user_id}: {e}")
        return ConversationHistory(user_id=user_id)
