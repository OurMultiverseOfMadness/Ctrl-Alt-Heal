"""History management utilities for intelligent conversation context handling."""

from __future__ import annotations

import re
from typing import List, Dict, Any, Tuple

from ctrl_alt_heal.domain.models import ConversationHistory, Message
from ctrl_alt_heal.utils.constants import (
    HISTORY_MAX_MESSAGES,
    HISTORY_MAX_TOKENS,
    HISTORY_KEEP_RECENT_MESSAGES,
    HISTORY_SUMMARY_MAX_LENGTH,
)


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string.
    Rough approximation: 1 token ≈ 4 characters for English text.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    # Rough approximation: 1 token ≈ 4 characters
    return len(text) // 4


def calculate_history_tokens(messages: List[Message]) -> int:
    """
    Calculate the estimated total tokens in conversation history.

    Args:
        messages: List of conversation messages

    Returns:
        Total estimated tokens
    """
    total_tokens = 0
    for message in messages:
        # Add tokens for role and content
        total_tokens += estimate_tokens(f"role: {message.role}")
        total_tokens += estimate_tokens(message.content)
        # Add overhead for message structure
        total_tokens += 10
    return total_tokens


def should_truncate_history(messages: List[Message]) -> bool:
    """
    Determine if history should be truncated based on message count and token limits.

    Args:
        messages: List of conversation messages

    Returns:
        True if history should be truncated
    """
    if len(messages) > HISTORY_MAX_MESSAGES:
        return True

    if calculate_history_tokens(messages) > HISTORY_MAX_TOKENS:
        return True

    return False


def extract_key_information(messages: List[Message]) -> Dict[str, Any]:
    """
    Extract key information from conversation history for summarization.

    Args:
        messages: List of conversation messages

    Returns:
        Dictionary containing key information
    """
    key_info: Dict[str, set] = {
        "topics": set(),
        "medications": set(),
        "timezones": set(),
        "user_preferences": set(),
        "important_dates": set(),
        "action_items": set(),
    }

    # Keywords to look for
    medication_keywords = [
        "medication",
        "prescription",
        "pill",
        "tablet",
        "capsule",
        "dose",
        "dosage",
    ]
    timezone_keywords = [
        "timezone",
        "time zone",
        "est",
        "pst",
        "gmt",
        "utc",
        "sgt",
        "jst",
    ]
    preference_keywords = ["prefer", "like", "dislike", "usually", "always", "never"]
    date_keywords = [
        "appointment",
        "schedule",
        "reminder",
        "today",
        "tomorrow",
        "next week",
    ]
    action_keywords = ["need to", "should", "must", "have to", "will", "going to"]

    for message in messages:
        content_lower = message.content.lower()

        # Extract medications
        for keyword in medication_keywords:
            if keyword in content_lower:
                # Look for medication names (capitalized words near medication keywords)
                words = message.content.split()
                for i, word in enumerate(words):
                    if keyword in word.lower() and i + 1 < len(words):
                        next_word = words[i + 1]
                        if next_word[0].isupper() and len(next_word) > 2:
                            key_info["medications"].add(next_word)

        # Extract timezones
        for keyword in timezone_keywords:
            if keyword in content_lower:
                key_info["timezones"].add(keyword.upper())

        # Extract preferences
        for keyword in preference_keywords:
            if keyword in content_lower:
                # Extract the sentence containing the preference
                sentences = re.split(r"[.!?]", message.content)
                for sentence in sentences:
                    if keyword in sentence.lower():
                        key_info["user_preferences"].add(sentence.strip())

        # Extract dates and appointments
        for keyword in date_keywords:
            if keyword in content_lower:
                key_info["important_dates"].add(keyword)

        # Extract action items
        for keyword in action_keywords:
            if keyword in content_lower:
                sentences = re.split(r"[.!?]", message.content)
                for sentence in sentences:
                    if keyword in sentence.lower():
                        key_info["action_items"].add(sentence.strip())

    # Convert sets to lists for JSON serialization
    return {k: list(v) for k, v in key_info.items()}


def create_history_summary(messages: List[Message]) -> str:
    """
    Create a summary of conversation history for context preservation.

    Args:
        messages: List of conversation messages to summarize

    Returns:
        Summary string
    """
    if not messages:
        return "No previous conversation history."

    key_info = extract_key_information(messages)

    summary_parts = []

    # Add conversation overview
    summary_parts.append(f"Previous conversation had {len(messages)} messages.")

    # Add key topics
    if key_info["medications"]:
        summary_parts.append(
            f"Discussed medications: {', '.join(key_info['medications'][:5])}"
        )

    if key_info["timezones"]:
        summary_parts.append(f"Timezone context: {', '.join(key_info['timezones'])}")

    if key_info["user_preferences"]:
        summary_parts.append(
            f"User preferences mentioned: {len(key_info['user_preferences'])} items"
        )

    if key_info["action_items"]:
        summary_parts.append(
            f"Action items discussed: {len(key_info['action_items'])} items"
        )

    # Add recent context
    recent_messages = messages[-5:] if len(messages) > 5 else messages
    recent_context = []
    for msg in recent_messages:
        role = "User" if msg.role == "user" else "Assistant"
        # Truncate long messages
        content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
        recent_context.append(f"{role}: {content}")

    summary_parts.append("Recent conversation context:")
    summary_parts.extend(recent_context)

    summary = "\n".join(summary_parts)

    # Truncate if too long
    if len(summary) > HISTORY_SUMMARY_MAX_LENGTH:
        summary = summary[:HISTORY_SUMMARY_MAX_LENGTH] + "..."

    return summary


def truncate_history_for_context(history: ConversationHistory) -> ConversationHistory:
    """
    Intelligently truncate conversation history while preserving important context.

    Args:
        history: Conversation history to truncate

    Returns:
        Truncated conversation history
    """
    if not should_truncate_history(history.history):
        return history

    # Create a new history object
    truncated_history = ConversationHistory(
        user_id=history.user_id,
        session_id=history.session_id,
        state=history.state.copy(),
        last_updated=history.last_updated,
    )

    # Always keep the most recent messages
    recent_messages = history.history[-HISTORY_KEEP_RECENT_MESSAGES:]

    # Create summary of older messages
    older_messages = history.history[:-HISTORY_KEEP_RECENT_MESSAGES]
    if older_messages:
        summary = create_history_summary(older_messages)
        summary_message = Message(
            role="system", content=f"Previous conversation summary: {summary}"
        )
        truncated_history.history = [summary_message] + recent_messages
    else:
        truncated_history.history = recent_messages

    return truncated_history


def get_optimized_history_for_agent(
    history: ConversationHistory,
) -> List[Dict[str, Any]]:
    """
    Get optimized conversation history for agent context injection.

    Args:
        history: Conversation history object

    Returns:
        List of messages optimized for agent context
    """
    # Truncate history if needed
    optimized_history = truncate_history_for_context(history)

    # Convert to agent format
    messages = []
    for message in optimized_history.history:
        messages.append({"role": message.role, "content": [{"text": message.content}]})

    return messages


def analyze_history_usage(history: ConversationHistory) -> Dict[str, Any]:
    """
    Analyze history usage and provide insights for optimization.

    Args:
        history: Conversation history to analyze

    Returns:
        Analysis results
    """
    messages = history.history
    total_tokens = calculate_history_tokens(messages)

    return {
        "message_count": len(messages),
        "estimated_tokens": total_tokens,
        "should_truncate": should_truncate_history(messages),
        "token_usage_percentage": (total_tokens / HISTORY_MAX_TOKENS) * 100,
        "recent_messages_count": min(len(messages), HISTORY_KEEP_RECENT_MESSAGES),
        "key_topics": extract_key_information(messages),
    }


def create_smart_history_summary(history: ConversationHistory) -> str:
    """
    Create a smart summary of the entire conversation history.

    Args:
        history: Conversation history to summarize

    Returns:
        Smart summary string
    """
    if not history.history:
        return "No conversation history available."

    analysis = analyze_history_usage(history)
    key_info = analysis["key_topics"]

    summary_parts = [
        "Conversation Summary:",
        f"- Total messages: {analysis['message_count']}",
        f"- Estimated tokens: {analysis['estimated_tokens']}",
        f"- Token usage: {analysis['token_usage_percentage']:.1f}%",
    ]

    if key_info["medications"]:
        summary_parts.append(
            f"- Medications discussed: {', '.join(key_info['medications'][:3])}"
        )

    if key_info["timezones"]:
        summary_parts.append(f"- Timezone context: {', '.join(key_info['timezones'])}")

    if key_info["action_items"]:
        summary_parts.append(f"- Action items: {len(key_info['action_items'])} pending")

    return "\n".join(summary_parts)


def should_create_new_session_due_to_history_size(
    history: ConversationHistory,
) -> Tuple[bool, str]:
    """
    Determine if a new session should be created due to history size constraints.

    Args:
        history: Conversation history to evaluate

    Returns:
        Tuple of (should_create, reason)
    """
    if not history.history:
        return False, "No history to evaluate"

    analysis = analyze_history_usage(history)

    if analysis["message_count"] > HISTORY_MAX_MESSAGES * 2:
        return True, f"History too large ({analysis['message_count']} messages)"

    if analysis["token_usage_percentage"] > 150:  # 150% of limit
        return True, f"Token usage too high ({analysis['token_usage_percentage']:.1f}%)"

    return False, "History size acceptable"


def cleanup_history_state(history: ConversationHistory) -> ConversationHistory:
    """
    Clean up history state and remove unnecessary data.

    Args:
        history: Conversation history to clean up

    Returns:
        Cleaned conversation history
    """
    # Remove any temporary state that shouldn't persist
    cleaned_state = {}
    for key, value in history.state.items():
        if not key.startswith("temp_") and not key.startswith("debug_"):
            cleaned_state[key] = value

    history.state = cleaned_state
    return history
