from typing import Any

from strands import tool

from ctrl_alt_heal.infrastructure.fhir_store import FhirStore


@tool(
    name="fhir_data",
    description="Stores FHIR data in S3 and DynamoDB.",
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "bundle": {"type": "object"},
        },
        "required": ["user_id", "bundle"],
    },
)
def fhir_data_tool(user_id: str, bundle: dict[str, Any]) -> str:
    """A tool for storing FHIR data."""
    store = FhirStore()
    return store.save_bundle(user_id, bundle)
