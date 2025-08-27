from unittest.mock import patch, Mock

from src.ctrl_alt_heal.tools.prescription_extraction_tool import (
    prescription_extraction_tool,
)


@patch("src.ctrl_alt_heal.tools.prescription_extraction_tool.settings")
@patch("src.ctrl_alt_heal.tools.prescription_extraction_tool.BedrockExtractor")
@patch("src.ctrl_alt_heal.tools.prescription_extraction_tool.extract_prescription")
def test_prescription_extraction_tool(
    mock_extract_prescription, mock_bedrock_extractor, mock_settings
):
    mock_settings.bedrock_model_id = "test_model"
    mock_bedrock_extractor.return_value = Mock()
    mock_extract_prescription.return_value = Mock(raw_json={"result": "success"})

    result = prescription_extraction_tool("test-bucket", "test-key", "test-user-id")

    assert result == {"result": "success"}
    mock_bedrock_extractor.assert_called_once_with(model_id="test_model")
    mock_extract_prescription.assert_called_once()
