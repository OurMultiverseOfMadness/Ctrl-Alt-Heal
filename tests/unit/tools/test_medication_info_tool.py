from unittest.mock import patch, Mock

from src.ctrl_alt_heal.tools.medication_info_tool import medication_info_tool


@patch("src.ctrl_alt_heal.tools.medication_info_tool.DDGS")
def test_medication_info_tool(mock_ddgs):
    mock_ddgs_instance = Mock()
    mock_ddgs.return_value.__enter__.return_value = mock_ddgs_instance
    mock_ddgs_instance.text.return_value = ["result1", "result2"]

    result = medication_info_tool("aspirin")

    assert result == "result1\nresult2"
    mock_ddgs_instance.text.assert_called_once_with("aspirin", max_results=5)
