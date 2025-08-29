import json
import os
from unittest.mock import patch, Mock
from src.ctrl_alt_heal.main import handler


@patch.dict(
    os.environ,
    {
        "USERS_TABLE_NAME": "ctrl-alt-heal-users",
        "CONVERSATIONS_TABLE_NAME": "ctrl-alt-heal-conversations",
        "IDENTITIES_TABLE_NAME": "ctrl-alt-heal-identities",
        "MESSAGES_QUEUE_URL": "https://sqs.test.amazonaws.com/test-queue",
    },
)
@patch("src.ctrl_alt_heal.main.boto3.client")
def test_handler_end_to_end(
    mock_boto3_client,
    history_table,
    users_table,
    identities_table,
):
    # Arrange
    mock_sqs = Mock()
    mock_boto3_client.return_value = mock_sqs

    event = {
        "body": json.dumps(
            {
                "message": {
                    "chat": {
                        "id": 12345,
                        "first_name": "Test",
                        "last_name": "User",
                        "username": "testuser",
                    },
                    "text": "Hello, world!",
                }
            }
        )
    }

    # Act
    result = handler(event, {})

    # Assert
    assert result["statusCode"] == 200
    mock_boto3_client.assert_called_once_with("sqs")
    mock_sqs.send_message.assert_called_once()

    # Verify the message was sent to SQS with the correct body
    call_args = mock_sqs.send_message.call_args
    assert call_args is not None
    message_body = json.loads(call_args[1]["MessageBody"])
    assert message_body["message"]["text"] == "Hello, world!"


@patch.dict(
    os.environ,
    {
        "USERS_TABLE_NAME": "ctrl-alt-heal-users",
        "CONVERSATIONS_TABLE_NAME": "ctrl-alt-heal-conversations",
        "IDENTITIES_TABLE_NAME": "ctrl-alt-heal-identities",
        "MESSAGES_QUEUE_URL": "https://sqs.test.amazonaws.com/test-queue",
    },
)
@patch("src.ctrl_alt_heal.main.boto3.client")
def test_handler_updates_timezone(
    mock_boto3_client,
    history_table,
    users_table,
    identities_table,
):
    # Arrange
    mock_sqs = Mock()
    mock_boto3_client.return_value = mock_sqs

    event = {
        "body": json.dumps(
            {
                "message": {
                    "chat": {"id": 12345},
                    "text": "Please set my timezone to America/Los_Angeles",
                }
            }
        )
    }

    # Act
    result = handler(event, {})

    # Assert
    assert result["statusCode"] == 200
    mock_boto3_client.assert_called_once_with("sqs")
    mock_sqs.send_message.assert_called_once()
