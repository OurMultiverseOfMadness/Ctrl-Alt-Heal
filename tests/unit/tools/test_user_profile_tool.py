from unittest.mock import patch, Mock

from src.ctrl_alt_heal.domain.models import User
from src.ctrl_alt_heal.tools.user_profile_tool import (
    update_user_profile_tool,
    get_user_profile_tool,
)


@patch("src.ctrl_alt_heal.tools.user_profile_tool.UsersStore")
def test_update_user_profile_tool(mock_users_store):
    # Arrange
    mock_store_instance = Mock()
    mock_users_store.return_value = mock_store_instance
    mock_user = User(
        user_id="test-user-id",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )
    mock_store_instance.get_user.return_value = mock_user

    # Act
    result = update_user_profile_tool(
        user_id="test-user-id", timezone="America/New_York", language="en"
    )

    # Assert
    assert result["status"] == "success"
    mock_store_instance.get_user.assert_called_once_with("test-user-id")
    mock_store_instance.upsert_user.assert_called_once()
    updated_user = mock_store_instance.upsert_user.call_args[0][0]
    assert updated_user.timezone == "America/New_York"
    assert updated_user.language == "en"


@patch("src.ctrl_alt_heal.tools.user_profile_tool.UsersStore")
def test_get_user_profile_tool(mock_users_store):
    # Arrange
    mock_store_instance = Mock()
    mock_users_store.return_value = mock_store_instance
    mock_user = User(
        user_id="test-user-id",
        first_name="Test",
        username="testuser",
        timezone="America/New_York",
        language="en",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )
    mock_store_instance.get_user.return_value = mock_user

    # Act
    result = get_user_profile_tool(user_id="test-user-id")

    # Assert
    assert result["status"] == "success"
    assert result["profile"]["first_name"] == "Test"
    assert result["profile"]["timezone"] == "America/New_York"
    mock_store_instance.get_user.assert_called_once_with("test-user-id")
