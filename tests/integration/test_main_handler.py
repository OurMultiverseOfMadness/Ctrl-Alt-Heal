import json
import os
from unittest.mock import patch, Mock
from src.ctrl_alt_heal.main import handler
from src.ctrl_alt_heal.domain.models import User, Identity
from datetime import datetime
from pytz import UTC


@patch.dict(
    os.environ,
    {
        "USERS_TABLE_NAME": "ctrl-alt-heal-users",
        "HISTORY_TABLE_NAME": "ctrl-alt-heal-history",
        "IDENTITIES_TABLE_NAME": "ctrl-alt-heal-identities",
    },
)
@patch("src.ctrl_alt_heal.main.get_agent")
@patch("src.ctrl_alt_heal.main.TelegramClient")
def test_handler_end_to_end(
    mock_telegram_client,
    mock_get_agent,
    history_table,
    users_table,
    identities_table,
):
    # Arrange
    mock_agent = Mock()
    mock_agent.invoke.return_value = "Test response"
    mock_get_agent.return_value = mock_agent

    mock_telegram_instance = Mock()
    mock_telegram_client.return_value = mock_telegram_instance

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
    mock_get_agent.assert_called_once()
    mock_agent.invoke.assert_called_once_with({"input": "Hello, world!"})
    mock_telegram_instance.send_message.assert_called_once_with(
        "12345", "Test response"
    )

    # Verify user is created/updated
    identity_response = identities_table.get_item(
        Key={"identity_key": "telegram#12345"}
    )
    identity_item = identity_response.get("Item")
    assert identity_item is not None
    user_id = identity_item["user_id"]

    user_response = users_table.get_item(Key={"user_id": user_id})
    user_item = user_response.get("Item")
    assert user_item is not None
    assert user_item["first_name"] == "Test"
    assert user_item["username"] == "testuser"

    # Verify history is saved
    history_response = history_table.get_item(Key={"user_id": user_id})
    history_item = history_response.get("Item")
    assert history_item is not None
    assert history_item["history"][-1]["content"] == "Test response"
    assert history_item["history"][-2]["content"] == "Hello, world!"


@patch.dict(
    os.environ,
    {
        "USERS_TABLE_NAME": "ctrl-alt-heal-users",
        "HISTORY_TABLE_NAME": "ctrl-alt-heal-history",
        "IDENTITIES_TABLE_NAME": "ctrl-alt-heal-identities",
    },
)
@patch("src.ctrl_alt_heal.main.get_agent")
@patch("src.ctrl_alt_heal.main.TelegramClient")
def test_handler_updates_timezone(
    mock_telegram_client,
    mock_get_agent,
    history_table,
    users_table,
    identities_table,
):
    # Arrange
    # First, create a user and identity to simulate an existing user
    now = datetime.now(UTC).isoformat()
    user = User(user_id="test-user-id", created_at=now, updated_at=now)
    users_table.put_item(Item=user.model_dump())
    identity = Identity(
        provider="telegram",
        provider_user_id="12345",
        user_id="test-user-id",
        created_at=now,
    )
    identities_table.put_item(
        Item={
            "identity_key": f"{identity.provider}#{identity.provider_user_id}",
            "user_id": identity.user_id,
        }
    )

    mock_agent = Mock()
    # Simulate the agent deciding to call the update_user_profile_tool
    mock_agent.invoke.return_value = {
        "tool_calls": [
            {
                "name": "update_user_profile_tool",
                "args": {"user_id": "test-user-id", "timezone": "America/Los_Angeles"},
            }
        ]
    }
    mock_get_agent.return_value = mock_agent

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
    handler(event, {})

    # Assert
    # We don't check for a message back to the user in this case,
    # as the agent loop would continue. We just verify the DB update.
    user_response = users_table.get_item(Key={"user_id": "test-user-id"})
    user_item = user_response.get("Item")
    assert user_item is not None
    assert user_item["timezone"] == "America/Los_Angeles"
