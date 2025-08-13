# Please delete this once done
import sys

sys.path.append("../../../..")
import os

from application.use_cases.extract_prescription import extract_prescription
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
from strands_tools import image_reader

if __name__ == "__main__":
    """
    In this demo, the image is read from a file and passed to the Nova Pro
    model using the image_reader tool.

    Example ToolResult (truncated):

        {
            'toolUseId': 'tooluse_abc123',
            'status': 'success',
            'content': [
                {
                    'image': {
                        'format': 'jpeg',
                        'source': {'bytes': b'...'}
                    }
                }
            ]
        }

    The results of the image_reader will be passed to the Nova Pro model to
    be interpreted and summarised.

    Then, the extract_prescription tool will extract the information into the
    Prescription data model.

    If you need the actual Python object, you have to call the tool manually.
    """

    print("#" * 50)
    print("This is for **LOCAL** demo only!!")
    print("#" * 50)

    if load_dotenv():
        if not os.getenv("AWS_BEARER_TOKEN_BEDROCK", None):
            raise ValueError("AWS Bedrock API token not found!")
        else:
            print("AWS Bedrock API token!")

        bedrock_model = BedrockModel(
            model_id="apac.amazon.nova-pro-v1:0", region_name="ap-southeast-1"
        )

        agent = Agent(
            model=bedrock_model,
            tools=[image_reader, extract_prescription],
            system_prompt=(
                "Your job is to help patients remember to take their medication on "
                "time and in the right amounts/dosage/method of administration. "
                "You will receive information on the medication they are prescribed "
                "and you need to extract and summarise that information for them. "
                "Finally you must use the extract_prescription tool to extract the "
                "required information in a machine-readable format. "
                "Reply only with the JSON representation of the Prescription."
            ),
        )

        result = agent("./assets/image.jpg")

    else:
        print(
            "Ensure you have a .env file with the following keys:\n"
            "-AWS_ACCESS_KEY_ID\n-AWS_SECRET_ACCESS_KEY\n-AWS_BEARER_TOKEN_BEDROCK"
        )
