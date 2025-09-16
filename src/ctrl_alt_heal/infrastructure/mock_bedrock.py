"""
Mock Bedrock implementation for local development.

This module provides mock implementations of Bedrock services that can be used
for local development and testing without requiring actual Bedrock access.
"""

import logging
from dataclasses import dataclass

from ctrl_alt_heal.tools.prescription_extractor import (
    ExtractionInput,
    ExtractionResult,
    PrescriptionExtractor,
)
from ctrl_alt_heal.domain.models import Prescription

logger = logging.getLogger(__name__)


@dataclass
class MockBedrock(PrescriptionExtractor):
    """Mock Bedrock implementation for local development."""

    model_id: str = "mock.amazon.nova-lite-v1:0"
    region_name: str | None = None

    def extract(self, data: ExtractionInput) -> ExtractionResult:
        """Mock prescription extraction for local development."""
        logger.info(
            f"Mock Bedrock extracting prescription from {data.s3_bucket}/{data.s3_key}"
        )

        # Return mock prescription data
        mock_prescriptions = [
            {
                "name": "Mock Medication A",
                "dosage": "500mg",
                "frequency": "twice daily",
                "duration_days": 30,
                "totalAmount": 60,
                "additionalInstructions": "Take with food. Mock prescription for local development.",
            },
            {
                "name": "Mock Medication B",
                "dosage": "10mg",
                "frequency": "once daily",
                "duration_days": 14,
                "totalAmount": 14,
                "additionalInstructions": "Take in the morning. Mock prescription for local development.",
            },
        ]

        # Create mock prescriptions
        prescriptions: list[Prescription] = []
        for med_data in mock_prescriptions:
            prescription = Prescription(
                name=med_data["name"],
                dosage=med_data["dosage"],
                frequency=med_data["frequency"],
                duration_days=med_data["duration_days"],
                totalAmount=med_data["totalAmount"],
                additionalInstructions=med_data["additionalInstructions"],
            )
            prescriptions.append(prescription)

        return ExtractionResult(
            prescriptions=prescriptions,
            raw_json={"mock_data": mock_prescriptions},
            confidence=0.95,
        )


def get_mock_bedrock() -> MockBedrock:
    """Get a mock Bedrock instance for local development."""
    logger.info("Using mock Bedrock for local development")
    return MockBedrock()
