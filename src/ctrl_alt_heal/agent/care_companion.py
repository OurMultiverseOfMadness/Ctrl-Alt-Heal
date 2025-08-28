from __future__ import annotations

import os
import boto3
from functools import lru_cache

from strands import Agent
from strands.models.bedrock import BedrockModel

from ctrl_alt_heal.domain.models import ConversationHistory

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
            # Temporarily disable automatic tool handling to prevent conflicts
            # Tools will be handled manually via the tool registry
        ],
    )
    return agent
