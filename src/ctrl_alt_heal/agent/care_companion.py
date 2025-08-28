from __future__ import annotations

import os
import boto3
from functools import lru_cache

from strands import Agent
from strands.models.bedrock import BedrockModel

from ctrl_alt_heal.domain.models import ConversationHistory
from ctrl_alt_heal.tools.calendar_tool import calendar_ics_tool
from ctrl_alt_heal.tools.fhir_data_tool import fhir_data_tool
from ctrl_alt_heal.tools.image_description_tool import describe_image_tool
from ctrl_alt_heal.tools.search_tool import search_tool
from ctrl_alt_heal.tools.prescription_extraction_tool import (
    prescription_extraction_tool,
)
from ctrl_alt_heal.tools.user_profile_tool import (
    get_user_profile_tool,
    save_user_notes_tool,
    update_user_profile_tool,
)
from ctrl_alt_heal.tools.identity_tool import (
    find_user_by_identity_tool,
    create_user_with_identity_tool,
    get_or_create_user_tool,
)
from ctrl_alt_heal.tools.timezone_tool import (
    detect_user_timezone_tool,
    suggest_timezone_from_language_tool,
)
from ctrl_alt_heal.tools.medication_schedule_tool import (
    set_medication_schedule_tool,
    get_medication_schedule_tool,
    clear_medication_schedule_tool,
)
from ctrl_alt_heal.tools.medication_ics_tool import (
    generate_medication_ics_tool,
    generate_single_medication_ics_tool,
)

# from ctrl_alt_heal.tools.google_auth_tool import (
#     exchange_code_for_token_tool,
#     generate_auth_url_tool,
# )
# from ctrl_alt_heal.tools.google_calendar_tool import (
#     create_google_calendar_event_tool,
#     delete_google_calendar_event_tool,
#     list_google_calendar_events_tool,
#     update_google_calendar_event_tool,
# )
from ctrl_alt_heal.domain.models import User

s3 = boto3.client("s3")


@lru_cache(maxsize=1)
def get_system_prompt() -> str:
    """
    Fetches the system prompt from S3.
    The result is cached in memory for the lifetime of the Lambda container.
    """
    bucket = os.environ["ASSETS_BUCKET_NAME"]
    key = "system_prompt.txt"
    response = s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read().decode("utf-8")


def get_agent(
    user: User, conversation_history: ConversationHistory | None = None
) -> Agent:
    """Returns a new agent instance on every invocation."""
    base_system_prompt = get_system_prompt()

    # Enhance system prompt with user context and notes
    user_context = f"User context: user_id={user.user_id}, first_name='{user.first_name}', last_name='{user.last_name}', username='{user.username}'"

    system_prompt_parts = [base_system_prompt, user_context]

    if user.notes:
        system_prompt_parts.append(f"Important notes about this user: {user.notes}")

    system_prompt = "\n\n".join(system_prompt_parts)

    messages = []

    # Add the current conversation history
    if conversation_history:
        for m in conversation_history.history:
            messages.append({"role": m.role, "content": [{"text": m.content}]})

    # Create a bedrock model instance
    bedrock_model = BedrockModel(
        model_id="apac.amazon.nova-lite-v1:0",
        region_name="ap-southeast-1",
        streaming=False,
    )

    agent = Agent(
        model=bedrock_model,
        system_prompt=system_prompt,
        messages=messages,
        tools=[
            describe_image_tool,
            prescription_extraction_tool,
            fhir_data_tool,
            calendar_ics_tool,
            search_tool,
            update_user_profile_tool,
            get_user_profile_tool,
            save_user_notes_tool,
            find_user_by_identity_tool,
            create_user_with_identity_tool,
            get_or_create_user_tool,
            detect_user_timezone_tool,
            suggest_timezone_from_language_tool,
            set_medication_schedule_tool,
            get_medication_schedule_tool,
            clear_medication_schedule_tool,
            generate_medication_ics_tool,
            generate_single_medication_ics_tool,
        ],
    )
    return agent
