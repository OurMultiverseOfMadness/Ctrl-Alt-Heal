"""Main entry point for the Ctrl-Alt-Heal application."""

import json
import os
from typing import Any

import boto3


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """AWS Lambda handler for the Telegram webhook."""
    sqs = boto3.client("sqs")
    queue_url = os.environ["MESSAGES_QUEUE_URL"]

    # The event from API Gateway is a string that needs to be parsed
    body = json.loads(event.get("body", "{}"))

    # Send the entire message payload to the SQS queue
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(body),
    )

    # Return an immediate 200 OK response to Telegram
    return {"statusCode": 200, "body": "Message queued for processing."}
