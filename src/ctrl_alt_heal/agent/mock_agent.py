"""
Mock agent for local development when Bedrock is not available.

This module provides a mock implementation of the AI agent that can be used
for local development and testing without requiring Bedrock access.
"""

import logging
from typing import Any, Dict

from ctrl_alt_heal.domain.models import User, ConversationHistory

logger = logging.getLogger(__name__)


class MockAgent:
    """Mock agent for local development."""

    def __init__(
        self, user: User, conversation_history: ConversationHistory | None = None
    ):
        self.user = user
        self.conversation_history = conversation_history
        self.tools = []

    async def run(self, message: str) -> Dict[str, Any]:
        """Mock agent response for local development."""
        logger.info(f"Mock agent processing message: {message}")

        # Simple mock responses based on message content
        if "prescription" in message.lower() or "medication" in message.lower():
            return {
                "content": "I can help you with medication management! In a real deployment, I would process your prescription and create a medication schedule. For local development, this is a mock response.",
                "tool_calls": [],
                "usage": {"input_tokens": 10, "output_tokens": 20},
            }
        elif "schedule" in message.lower() or "reminder" in message.lower():
            return {
                "content": "I can help you set up medication reminders! In a real deployment, I would create a calendar schedule for your medications. For local development, this is a mock response.",
                "tool_calls": [],
                "usage": {"input_tokens": 10, "output_tokens": 25},
            }
        elif "hello" in message.lower() or "hi" in message.lower():
            return {
                "content": f"Hello {self.user.first_name}! I'm your healthcare companion. I'm running in mock mode for local development. I can help you with medication management, prescription processing, and health reminders.",
                "tool_calls": [],
                "usage": {"input_tokens": 10, "output_tokens": 30},
            }
        else:
            return {
                "content": "I'm your healthcare companion running in mock mode for local development. I can help you with medication management, prescription processing, and health reminders. In a real deployment, I would use AI to provide personalized healthcare assistance.",
                "tool_calls": [],
                "usage": {"input_tokens": 10, "output_tokens": 35},
            }


def get_mock_agent(
    user: User, conversation_history: ConversationHistory | None = None
) -> MockAgent:
    """Get a mock agent for local development."""
    logger.info("Using mock agent for local development")
    return MockAgent(user, conversation_history)
