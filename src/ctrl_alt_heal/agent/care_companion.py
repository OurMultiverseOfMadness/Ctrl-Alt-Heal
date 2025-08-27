from __future__ import annotations

import os

from strands import Agent
from strands.models.bedrock import BedrockModel

from ctrl_alt_heal.domain.models import ConversationHistory
from ctrl_alt_heal.tools.calendar_tool import calendar_ics_tool
from ctrl_alt_heal.tools.fhir_data_tool import fhir_data_tool
from ctrl_alt_heal.tools.google_auth_tool import (
    exchange_code_for_token_tool,
    generate_auth_url_tool,
)
from ctrl_alt_heal.tools.google_calendar_tool import (
    create_google_calendar_event_tool,
    delete_google_calendar_event_tool,
    list_google_calendar_events_tool,
    update_google_calendar_event_tool,
)
from ctrl_alt_heal.tools.search_tool import search_tool
from ctrl_alt_heal.tools.prescription_extraction_tool import (
    prescription_extraction_tool,
)
from ctrl_alt_heal.tools.user_profile_tool import (
    update_user_profile_tool,
)

_agent = None


def get_agent(
    conversation_history: ConversationHistory | None = None,
) -> Agent:
    """Returns a singleton agent instance."""
    global _agent
    if _agent is None:
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the full path to the system_prompt.txt file
        prompt_path = os.path.join(current_dir, "system_prompt.txt")
        with open(prompt_path) as f:
            system_prompt = f.read()

        messages = (
            [
                {"role": m.role, "content": [{"text": m.content}]}
                for m in conversation_history.history
            ]
            if conversation_history
            else []
        )

        # Create a bedrock model instance
        bedrock_model = BedrockModel(
            model_id="apac.amazon.nova-lite-v1:0",
            region_name="ap-southeast-1",
            streaming=False,
        )

        _agent = Agent(
            model=bedrock_model,
            system_prompt=system_prompt,
            messages=messages,
            tools=[
                prescription_extraction_tool,
                fhir_data_tool,
                calendar_ics_tool,
                search_tool,
                generate_auth_url_tool,
                exchange_code_for_token_tool,
                create_google_calendar_event_tool,
                list_google_calendar_events_tool,
                update_google_calendar_event_tool,
                delete_google_calendar_event_tool,
                update_user_profile_tool,
            ],
        )
    return _agent
