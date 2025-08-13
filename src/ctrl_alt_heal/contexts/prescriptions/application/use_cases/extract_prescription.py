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
    "You are a trained pharmacist experienced in reading prescriptions from doctors."
    " Analyze the provided image(s) and extract each medication with its dosage "
    "and frequency."
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
