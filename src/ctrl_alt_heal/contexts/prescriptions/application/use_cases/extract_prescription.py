from src.ctrl_alt_heal.config.settings import Settings
from src.ctrl_alt_heal.contexts.prescriptions.domain.prescription import Prescription
from strands import Agent, tool
from strands.models import BedrockModel
import boto3
import os
from dotenv import load_dotenv


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
    "You are a trained pharmacists who is experienced in reading prescriptions from doctors"
    "Analyse the image you are given and extract the names of the medication and the corresponding dosage and frequencies from the images"
)


@tool(
    description="Reads a prescription summary and returns a Prescription Python object",
    inputSchema=INPUT_SCHEMA,
)
def extract_prescription(summary) -> Prescription | None:
    """
    Given a string summary of the prescription label extracted, summarise the information in to a machine readable format using the Prescription Python
    pydantic data model.
    """

    agent = Agent(model=bedrock_model, system_prompt=prescription_extraction_prompt)

    try:
        results = agent.structured_output(Prescription, [{"text": summary}])

    except Exception as e:
        print(e)
        return None

    else:
        return results
