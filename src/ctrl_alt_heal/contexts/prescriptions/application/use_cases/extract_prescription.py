from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel

from src.ctrl_alt_heal.config.settings import Settings
from src.ctrl_alt_heal.contexts.prescriptions.domain.prescription import Prescription

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A summary of all the information on the prescription.",
        }
    },
}

load_dotenv()

settings = Settings.load()

# session = boto3.Session(
#     region_name=settings.aws_region,
#     aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#     aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
# )

bedrock_model = BedrockModel(
    # boto_session=session,
    model_id=settings.bedrock_extract_model_id
    if settings.bedrock_extract_model_id
    else "apac.amazon.nova-lite-v1:0",
    region_name=settings.aws_region,
)

prescription_extraction_prompt = (
    "You are a clinical pharmacist. Extract a single medication from a patient "
    "prescription and map it to the Prescription model fields.\n\n"
    "Rules:\n"
    "- Focus on one medication for this call.\n"
    "- Fill fields: name, dosage (free text), frequency (free text), totalAmount, "
    "additionalInstructions.\n"
    "- Normalise common abbreviations in frequency where possible (e.g., BID→2x/day,"
    " TDS→3x/day) but keep original in free text.\n"
    "- If a field is unknown or illegible, leave it empty and add context in "
    "additionalInstructions (e.g., 'illegible strength').\n"
    "- Do not hallucinate missing data.\n"
    "- Use source wording when uncertain.\n"
)

multi_prescription_extraction_prompt = (
    "You are a clinical pharmacist. Extract all medications from a prescription and "
    "map them to the following JSON array of Prescription objects.\n\n"
    "Rules:\n"
    "- Return a JSON array of items, one per medication.\n"
    "- For each item, fill: name, dosage (free text), frequency (free text), "
    "totalAmount, additionalInstructions.\n"
    "- Normalise freq. when possible (BID→2x/day, TDS→3x/day) and keep the original "
    "in free text.\n"
    "- Unknown/illegible: leave empty and note the reason in additionalInstructions.\n"
    "- Do not hallucinate missing data. Use source wording when uncertain.\n"
)


@tool(
    description="Reads a prescription summary and returns a Prescription Python object",
    inputSchema=INPUT_SCHEMA,
)
def extract_prescription(summary) -> Prescription | None:
    """
    Summarise the extracted prescription label into the Prescription
    pydantic data model (machine-readable format).
    """

    agent = Agent(model=bedrock_model, system_prompt=prescription_extraction_prompt)

    try:
        results = agent.structured_output(Prescription, [{"text": summary}])

    except Exception as e:
        print(e)
        return None

    else:
        return results


@tool(
    description=(
        "Reads a prescription summary and returns a list of Prescription Python objects"
    ),
    inputSchema=INPUT_SCHEMA,
)
def extract_prescriptions_list(summary) -> list[Prescription] | None:
    """
    Summarise the extracted prescription label into a list of Prescription
    objects (machine-readable format) when multiple medications are present.
    """

    agent = Agent(
        model=bedrock_model, system_prompt=multi_prescription_extraction_prompt
    )

    try:
        # Expect an array of Prescription models
        results: list[Prescription] = agent.structured_output(  # type: ignore[assignment]
            list[Prescription],
            [{"text": summary}],
        )
    except Exception as e:
        print(e)
        return None
    else:
        return results
