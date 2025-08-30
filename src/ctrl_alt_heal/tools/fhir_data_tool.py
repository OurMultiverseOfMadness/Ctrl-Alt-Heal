from typing import Any

from strands import tool

from ctrl_alt_heal.tools.fhir_store import FhirStore


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
    # Convert user_id to int if it's a numeric string, otherwise use a hash
    try:
        user_id_int = int(user_id)
    except ValueError:
        # If user_id is not numeric, use a hash of the string
        user_id_int = hash(user_id) % (2**31)  # Keep within int range
    return store.save_bundle(user_id_int, bundle)
