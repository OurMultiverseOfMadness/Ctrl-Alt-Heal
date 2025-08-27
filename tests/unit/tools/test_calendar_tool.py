from unittest.mock import patch

from src.ctrl_alt_heal.tools.calendar_tool import calendar_ics_tool


@patch("src.ctrl_alt_heal.tools.calendar_tool.Calendar")
def test_calendar_ics_tool(mock_calendar):
    mock_calendar_instance = mock_calendar.return_value
    mock_calendar_instance.__str__.return_value = "ICS_FILE_CONTENT"

    result = calendar_ics_tool(
        "Meeting", "2024-01-01T10:00:00Z", "2024-01-01T11:00:00Z"
    )

    assert result == "ICS_FILE_CONTENT"
    mock_calendar.assert_called_once()
