from unittest.mock import patch, Mock

from src.ctrl_alt_heal.tools.google_calendar_tool import (
    create_google_calendar_event_tool,
)


@patch("src.ctrl_alt_heal.tools.google_calendar_tool.UsersStore")
@patch("src.ctrl_alt_heal.tools.google_calendar_tool.GoogleCalendarClient")
def test_create_google_calendar_event_tool(mock_gcal_client, mock_users_store):
    # Arrange
    mock_gcal_client_instance = Mock()
    mock_gcal_client.return_value = mock_gcal_client_instance
    mock_gcal_client_instance.create_event.return_value = {"status": "success"}

    mock_users_store_instance = Mock()
    mock_users_store.return_value = mock_users_store_instance

    # Act
    result = create_google_calendar_event_tool(
        "test-user-id", "Meeting", "2024-01-01T10:00:00Z", "2024-01-01T11:00:00Z"
    )

    # Assert
    assert result == {"status": "success"}
    mock_users_store.assert_called_once()
    mock_gcal_client.assert_called_once_with("test-user-id", mock_users_store_instance)
    mock_gcal_client_instance.create_event.assert_called_once_with(
        "Meeting", "2024-01-01T10:00:00Z", "2024-01-01T11:00:00Z"
    )
