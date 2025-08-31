from unittest.mock import patch, Mock

from src.ctrl_alt_heal.tools.fhir_data_tool import fhir_data_tool


@patch("src.ctrl_alt_heal.tools.fhir_data_tool.FhirStore")
def test_fhir_data_tool(mock_fhir_store):
    mock_fhir_store_instance = Mock()
    mock_fhir_store.return_value = mock_fhir_store_instance
    mock_fhir_store_instance.save_bundle.return_value = "sk-123"

    result = fhir_data_tool("test-user-id", {"bundle": "data"})

    assert result == "sk-123"
    mock_fhir_store.assert_called_once()
    # The function now passes user_id as string directly
    mock_fhir_store_instance.save_bundle.assert_called_once_with(
        "test-user-id", {"bundle": "data"}
    )
