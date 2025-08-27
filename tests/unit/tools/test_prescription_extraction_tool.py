from unittest.mock import MagicMock, patch

from ctrl_alt_heal.domain.models import ExtractionInput, ExtractionResult
from ctrl_alt_heal.tools.prescription_extraction_tool import (
    prescription_extraction_tool,
)


@patch("src.ctrl_alt_heal.tools.prescription_extraction_tool.Bedrock")
def test_prescription_extraction_tool(mock_bedrock_constructor):
    """Tests the prescription_extraction_tool."""
    # Arrange
    mock_extractor_instance = MagicMock()
    mock_extractor_instance.extract.return_value = ExtractionResult(
        raw_json={"status": "success"}, confidence=0.9
    )
    mock_bedrock_constructor.return_value = mock_extractor_instance

    # Act
    result = prescription_extraction_tool(
        user_id="test-user",
        s3_bucket="test-bucket",
        s3_key="test-key",
    )

    # Assert
    assert result == {"status": "success"}
    mock_bedrock_constructor.assert_called_once()
    mock_extractor_instance.extract.assert_called_once_with(
        ExtractionInput(
            user_id="test-user",
            s3_bucket="test-bucket",
            s3_key="test-key",
        )
    )
