from __future__ import annotations

import json
from typing import Any

import boto3


class SecretsStore:
    def __init__(self) -> None:
        self.client = boto3.client("secretsmanager")

    def save_secret(self, secret_name: str, secret_value: dict[str, Any]) -> None:
        """Saves a secret to AWS Secrets Manager."""
        self.client.put_secret_value(
            SecretId=secret_name, SecretString=json.dumps(secret_value)
        )

    def get_secret(self, secret_name: str) -> dict[str, Any] | None:
        """Retrieves a secret from AWS Secrets Manager."""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response["SecretString"])
        except self.client.exceptions.ResourceNotFoundException:
            return None
