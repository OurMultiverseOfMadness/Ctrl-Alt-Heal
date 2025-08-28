"""Tests for prescription extractor linking functionality."""

from unittest.mock import MagicMock, patch


from ctrl_alt_heal.domain.models import Prescription
from ctrl_alt_heal.tools.prescription_extractor import (
    ExtractionInput,
    ExtractionResult,
    extract_prescription,
)


@patch("ctrl_alt_heal.tools.prescription_extractor.FhirStore")
@patch("ctrl_alt_heal.tools.prescription_extractor.PrescriptionsStore")
def test_extract_prescription_links_fhir_bundle_to_prescription(
    mock_prescriptions_store_class, mock_fhir_store_class
):
    """Test that prescription and FHIR bundle are properly linked after extraction."""
    # Arrange
    mock_prescriptions_store = MagicMock()
    mock_fhir_store = MagicMock()

    mock_prescriptions_store_class.return_value = mock_prescriptions_store
    mock_fhir_store_class.return_value = mock_fhir_store

    # Mock return values
    prescription_sk = "PRESCRIPTION#123-456-789"
    bundle_sk = "BUNDLE#987-654-321"
    mock_prescriptions_store.save_prescription.return_value = prescription_sk
    mock_fhir_store.save_bundle.return_value = bundle_sk

    # Create test prescription
    test_prescription = Prescription(
        name="Test Medication",
        dosage="1 tablet",
        frequency="twice daily",
        totalAmount="30 tablets",
    )

    # Mock extractor
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = ExtractionResult(
        raw_json={"medications": [test_prescription.model_dump()]},
        confidence=0.9,
        prescriptions=[test_prescription],
    )

    user_id = "test-user-123"
    extraction_input = ExtractionInput(s3_bucket="test-bucket", s3_key="test-key")

    # Act
    result = extract_prescription(mock_extractor, extraction_input, user_id)

    # Assert
    assert result.prescriptions is not None
    assert len(result.prescriptions) == 1

    # Verify prescription was saved
    mock_prescriptions_store.save_prescription.assert_called_once_with(
        user_id=user_id,
        name="Test Medication",
        dosage_text="1 tablet",
        frequency_text="twice daily",
        status="active",
        source_bundle_sk=None,  # Initially None
        start_iso=None,
    )

    # Verify FHIR bundle was saved
    mock_fhir_store.save_bundle.assert_called_once()
    call_args = mock_fhir_store.save_bundle.call_args
    assert call_args[1]["user_id"] == user_id
    # Check that a FHIR bundle was created
    bundle = call_args[1]["bundle"]
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "transaction"

    # Verify the prescription was linked to the FHIR bundle
    mock_prescriptions_store.update_prescription_source_bundle.assert_called_once_with(
        user_id=user_id, sk=prescription_sk, source_bundle_sk=bundle_sk
    )


@patch("ctrl_alt_heal.tools.prescription_extractor.FhirStore")
@patch("ctrl_alt_heal.tools.prescription_extractor.PrescriptionsStore")
def test_extract_prescription_links_multiple_prescriptions(
    mock_prescriptions_store_class, mock_fhir_store_class
):
    """Test that multiple prescriptions are properly linked to their respective FHIR bundles."""
    # Arrange
    mock_prescriptions_store = MagicMock()
    mock_fhir_store = MagicMock()

    mock_prescriptions_store_class.return_value = mock_prescriptions_store
    mock_fhir_store_class.return_value = mock_fhir_store

    # Mock return values for two prescriptions
    prescription_sks = ["PRESCRIPTION#111", "PRESCRIPTION#222"]
    bundle_sks = ["BUNDLE#aaa", "BUNDLE#bbb"]
    mock_prescriptions_store.save_prescription.side_effect = prescription_sks
    mock_fhir_store.save_bundle.side_effect = bundle_sks

    # Create test prescriptions
    prescriptions = [
        Prescription(
            name="Medication A",
            dosage="1 tablet",
            frequency="once daily",
            totalAmount="30 tablets",
        ),
        Prescription(
            name="Medication B",
            dosage="2 capsules",
            frequency="twice daily",
            totalAmount="60 capsules",
        ),
    ]

    # Mock extractor
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = ExtractionResult(
        raw_json={"medications": [p.model_dump() for p in prescriptions]},
        confidence=0.9,
        prescriptions=prescriptions,
    )

    user_id = "test-user-456"
    extraction_input = ExtractionInput(s3_bucket="test-bucket", s3_key="test-key")

    # Act
    result = extract_prescription(mock_extractor, extraction_input, user_id)

    # Assert
    assert result.prescriptions is not None
    assert len(result.prescriptions) == 2

    # Verify both prescriptions were saved
    assert mock_prescriptions_store.save_prescription.call_count == 2

    # Verify both FHIR bundles were saved
    assert mock_fhir_store.save_bundle.call_count == 2

    # Verify both prescriptions were linked to their respective FHIR bundles
    assert mock_prescriptions_store.update_prescription_source_bundle.call_count == 2

    # Check specific linking calls
    linking_calls = (
        mock_prescriptions_store.update_prescription_source_bundle.call_args_list
    )

    # First prescription linking
    assert linking_calls[0][1]["user_id"] == user_id
    assert linking_calls[0][1]["sk"] == prescription_sks[0]
    assert linking_calls[0][1]["source_bundle_sk"] == bundle_sks[0]

    # Second prescription linking
    assert linking_calls[1][1]["user_id"] == user_id
    assert linking_calls[1][1]["sk"] == prescription_sks[1]
    assert linking_calls[1][1]["source_bundle_sk"] == bundle_sks[1]


@patch("ctrl_alt_heal.tools.prescription_extractor.FhirStore")
@patch("ctrl_alt_heal.tools.prescription_extractor.PrescriptionsStore")
def test_extract_prescription_no_prescriptions_extracted(
    mock_prescriptions_store_class, mock_fhir_store_class
):
    """Test that no linking occurs when no prescriptions are extracted."""
    # Arrange
    mock_prescriptions_store = MagicMock()
    mock_fhir_store = MagicMock()

    mock_prescriptions_store_class.return_value = mock_prescriptions_store
    mock_fhir_store_class.return_value = mock_fhir_store

    # Mock extractor with no prescriptions
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = ExtractionResult(
        raw_json={"medications": []}, confidence=0.0, prescriptions=None
    )

    user_id = "test-user-789"
    extraction_input = ExtractionInput(s3_bucket="test-bucket", s3_key="test-key")

    # Act
    result = extract_prescription(mock_extractor, extraction_input, user_id)

    # Assert
    assert result.prescriptions is None

    # Verify no database operations occurred
    mock_prescriptions_store.save_prescription.assert_not_called()
    mock_fhir_store.save_bundle.assert_not_called()
    mock_prescriptions_store.update_prescription_source_bundle.assert_not_called()
