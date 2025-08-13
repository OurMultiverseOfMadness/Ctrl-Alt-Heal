# Please delete this once done
import sys

sys.path.append("../../../..")
import os
from dotenv import load_dotenv
from application.use_cases.extract_prescription import extract_prescription
from strands import Agent
from strands.models import BedrockModel
from strands_tools import image_reader


if __name__ == "__main__":
    """
    In this demo, the image is read from a file and passed to the Nova Pro model using the image_reader tool.
    
    The image_reader tool returns a ToolResult that looks like the following:

        {'toolUseId': 'tooluse_fZzLJHReR6SoF7aubr6xSw',
        'status': 'success',
        'content': [{'image': {'format': 'jpeg',
            'source': {'bytes': b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\'}
            
    The results of the image_reader will be passed to the Nova Pro model to be interpreted and summarised.
    
    Then, the extract_prescription tool will be used to extract the information into the Prescription data model.
    
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
                "Your job is to help patients remember to take their medication on time and in the right amounts/dosage/method of adminstration"
                "You will be receiving information on the medication that they are prescribed and you will need to extract and summarise that information for them."
                "Finally you must use the extract_prescription tool to extract the required information in a machine-readable format."
                "You are to reply only with the JSON representation of the Prescription"
            ),
        )

        result = agent("./assets/image.jpg")

        # print("#" * 50)
        # print("Agent details")
        # print("#" * 50)
        # print(agent.messages)
        # print(agent.state)

    else:
        print(
            "Ensure you have a .env file with the following keys:\n-AWS_ACCESS_KEY_ID\n-AWS_SECRET_ACCESS_KEY\n-AWS_BEARER_TOKEN_BEDROCK"
        )
