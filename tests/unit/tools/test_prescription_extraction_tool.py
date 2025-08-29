from unittest.mock import patch

from ctrl_alt_heal.tools.prescription_extractor import ExtractionResult
from ctrl_alt_heal.tools.prescription_extraction_tool import (
    prescription_extraction_tool,
)


@patch("ctrl_alt_heal.tools.prescription_extraction_tool.extract_prescription")
def test_prescription_extraction_tool(mock_extract_prescription):
    """Tests the prescription_extraction_tool."""
    # Arrange
    # Create a mock prescription
    from ctrl_alt_heal.domain.models import Prescription

    mock_prescription = Prescription(
        name="Test Medication",
        dosage="1 tablet",
        frequency="twice daily",
        totalAmount="14 tablets",
        additionalInstructions="Take with food",
    )

    mock_extract_prescription.return_value = ExtractionResult(
        raw_json={"status": "success"},
        confidence=0.9,
        prescriptions=[mock_prescription],
    )

    # Act
    result = prescription_extraction_tool(
        user_id="test-user",
        s3_bucket="test-bucket",
        s3_key="test-key",
    )

    # Assert
    expected_response = {
        "status": "success",
        "message": "Successfully extracted 1 prescription(s) from the image and saved them to your profile.",
        "prescriptions": [mock_prescription.model_dump()],
        "count": 1,
        "extraction_summary": {
            "total_medications": 1,
            "medication_names": ["Test Medication"],
            "extraction_confidence": 0.9,
        },
    }
    assert result == expected_response
    mock_extract_prescription.assert_called_once()
