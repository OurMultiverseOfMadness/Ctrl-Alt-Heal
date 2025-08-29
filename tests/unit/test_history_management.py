"""Unit tests for history management utilities."""

from ctrl_alt_heal.utils.history_management import (
    estimate_tokens,
    calculate_history_tokens,
    should_truncate_history,
    extract_key_information,
    create_history_summary,
    truncate_history_for_context,
    get_optimized_history_for_agent,
    analyze_history_usage,
    create_smart_history_summary,
    should_create_new_session_due_to_history_size,
    cleanup_history_state,
)
from ctrl_alt_heal.domain.models import ConversationHistory, Message
from ctrl_alt_heal.utils.constants import (
    HISTORY_MAX_MESSAGES,
    HISTORY_MAX_TOKENS,
    HISTORY_KEEP_RECENT_MESSAGES,
)


class TestTokenEstimation:
    """Test token estimation functionality."""

    def test_estimate_tokens_short_text(self):
        """Test token estimation for short text."""
        text = "Hello world"
        tokens = estimate_tokens(text)
        assert tokens == 2  # 11 characters / 4 ≈ 2

    def test_estimate_tokens_long_text(self):
        """Test token estimation for long text."""
        text = "This is a much longer text that should have more tokens"
        tokens = estimate_tokens(text)
        assert tokens == 13  # 52 characters / 4 ≈ 13

    def test_estimate_tokens_empty_text(self):
        """Test token estimation for empty text."""
        tokens = estimate_tokens("")
        assert tokens == 0

    def test_calculate_history_tokens_empty(self):
        """Test token calculation for empty history."""
        messages = []
        tokens = calculate_history_tokens(messages)
        assert tokens == 0

    def test_calculate_history_tokens_single_message(self):
        """Test token calculation for single message."""
        messages = [Message(role="user", content="Hello")]
        tokens = calculate_history_tokens(messages)
        # role: user (8 chars) + content (5 chars) + overhead (10) = 23 / 4 ≈ 5
        assert tokens > 0

    def test_calculate_history_tokens_multiple_messages(self):
        """Test token calculation for multiple messages."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!"),
            Message(role="user", content="How are you?"),
        ]
        tokens = calculate_history_tokens(messages)
        assert tokens > 0


class TestHistoryTruncation:
    """Test history truncation logic."""

    def test_should_truncate_history_under_limits(self):
        """Test that history under limits should not be truncated."""
        messages = [Message(role="user", content="Hello") for _ in range(10)]
        assert not should_truncate_history(messages)

    def test_should_truncate_history_message_count_exceeded(self):
        """Test that history with too many messages should be truncated."""
        messages = [
            Message(role="user", content="Hello")
            for _ in range(HISTORY_MAX_MESSAGES + 1)
        ]
        assert should_truncate_history(messages)

    def test_should_truncate_history_token_limit_exceeded(self):
        """Test that history with too many tokens should be truncated."""
        # Create a very long message that exceeds token limit
        long_content = "x" * (HISTORY_MAX_TOKENS * 4)  # Ensure we exceed token limit
        messages = [Message(role="user", content=long_content)]
        assert should_truncate_history(messages)


class TestKeyInformationExtraction:
    """Test key information extraction from messages."""

    def test_extract_key_information_medications(self):
        """Test extraction of medication information."""
        messages = [
            Message(role="user", content="I need to take my medication ZOCLEAR 500"),
            Message(role="assistant", content="I'll help you with your prescription"),
        ]
        key_info = extract_key_information(messages)
        assert "medications" in key_info
        assert len(key_info["medications"]) > 0

    def test_extract_key_information_timezones(self):
        """Test extraction of timezone information."""
        messages = [
            Message(role="user", content="I'm in EST timezone"),
            Message(role="assistant", content="I'll set your timezone to EST"),
        ]
        key_info = extract_key_information(messages)
        assert "timezones" in key_info
        assert "EST" in key_info["timezones"]

    def test_extract_key_information_preferences(self):
        """Test extraction of user preferences."""
        messages = [
            Message(role="user", content="I prefer to take medication in the morning"),
            Message(role="assistant", content="I'll note your preference"),
        ]
        key_info = extract_key_information(messages)
        assert "user_preferences" in key_info
        assert len(key_info["user_preferences"]) > 0

    def test_extract_key_information_action_items(self):
        """Test extraction of action items."""
        messages = [
            Message(role="user", content="I need to schedule an appointment"),
            Message(role="assistant", content="I'll help you with that"),
        ]
        key_info = extract_key_information(messages)
        assert "action_items" in key_info
        assert len(key_info["action_items"]) > 0

    def test_extract_key_information_empty_messages(self):
        """Test extraction with empty messages."""
        messages = []
        key_info = extract_key_information(messages)
        assert all(len(v) == 0 for v in key_info.values())


class TestHistorySummary:
    """Test history summary creation."""

    def test_create_history_summary_empty(self):
        """Test summary creation for empty history."""
        messages = []
        summary = create_history_summary(messages)
        assert "No previous conversation history" in summary

    def test_create_history_summary_with_medications(self):
        """Test summary creation with medication information."""
        messages = [
            Message(role="user", content="I take ZOCLEAR 500 medication"),
            Message(role="assistant", content="I'll help you manage your medication"),
        ]
        summary = create_history_summary(messages)
        assert "ZOCLEAR" in summary or "medications" in summary

    def test_create_history_summary_truncation(self):
        """Test that summary is truncated when too long."""
        # Create a very long message
        long_content = "x" * 2000
        messages = [Message(role="user", content=long_content)]
        summary = create_history_summary(messages)
        assert len(summary) <= 1000 + 3  # +3 for "..." if truncated


class TestHistoryTruncationForContext:
    """Test intelligent history truncation."""

    def test_truncate_history_for_context_no_truncation_needed(self):
        """Test that history is not truncated when not needed."""
        history = ConversationHistory(
            user_id="test-user",
            history=[Message(role="user", content="Hello") for _ in range(5)],
        )
        truncated = truncate_history_for_context(history)
        assert len(truncated.history) == len(history.history)

    def test_truncate_history_for_context_with_truncation(self):
        """Test that history is truncated when needed."""
        # Create history that exceeds limits
        history = ConversationHistory(
            user_id="test-user",
            history=[
                Message(role="user", content="Hello")
                for _ in range(HISTORY_MAX_MESSAGES + 10)
            ],
        )
        truncated = truncate_history_for_context(history)
        assert len(truncated.history) < len(history.history)
        assert (
            len(truncated.history) == HISTORY_KEEP_RECENT_MESSAGES + 1
        )  # +1 for summary

    def test_truncate_history_for_context_preserves_recent(self):
        """Test that recent messages are preserved during truncation."""
        history = ConversationHistory(
            user_id="test-user",
            history=[
                Message(role="user", content=f"Old message {i}")
                for i in range(60)  # Exceed HISTORY_MAX_MESSAGES (50)
            ]
            + [
                Message(role="user", content="Recent message 1"),
                Message(role="assistant", content="Recent response 1"),
                Message(role="user", content="Recent message 2"),
            ],
        )
        truncated = truncate_history_for_context(history)

        # Should have summary + recent messages
        assert len(truncated.history) == HISTORY_KEEP_RECENT_MESSAGES + 1
        assert truncated.history[0].role == "system"  # Summary message
        assert "Recent message" in truncated.history[-1].content


class TestOptimizedHistoryForAgent:
    """Test optimized history for agent context."""

    def test_get_optimized_history_for_agent_empty(self):
        """Test optimized history for empty conversation."""
        history = ConversationHistory(user_id="test-user")
        messages = get_optimized_history_for_agent(history)
        assert messages == []

    def test_get_optimized_history_for_agent_with_messages(self):
        """Test optimized history with messages."""
        history = ConversationHistory(
            user_id="test-user",
            history=[
                Message(role="user", content="Hello"),
                Message(role="assistant", content="Hi there!"),
            ],
        )
        messages = get_optimized_history_for_agent(history)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"][0]["text"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"][0]["text"] == "Hi there!"


class TestHistoryUsageAnalysis:
    """Test history usage analysis."""

    def test_analyze_history_usage_empty(self):
        """Test analysis of empty history."""
        history = ConversationHistory(user_id="test-user")
        analysis = analyze_history_usage(history)
        assert analysis["message_count"] == 0
        assert analysis["estimated_tokens"] == 0
        assert analysis["should_truncate"] is False
        assert analysis["token_usage_percentage"] == 0

    def test_analyze_history_usage_with_messages(self):
        """Test analysis of history with messages."""
        history = ConversationHistory(
            user_id="test-user",
            history=[
                Message(role="user", content="Hello"),
                Message(role="assistant", content="Hi there!"),
            ],
        )
        analysis = analyze_history_usage(history)
        assert analysis["message_count"] == 2
        assert analysis["estimated_tokens"] > 0
        assert "key_topics" in analysis

    def test_analyze_history_usage_large_history(self):
        """Test analysis of large history."""
        history = ConversationHistory(
            user_id="test-user",
            history=[
                Message(role="user", content="Hello")
                for _ in range(HISTORY_MAX_MESSAGES + 1)
            ],
        )
        analysis = analyze_history_usage(history)
        assert analysis["message_count"] > HISTORY_MAX_MESSAGES
        assert analysis["should_truncate"] is True


class TestSmartHistorySummary:
    """Test smart history summary creation."""

    def test_create_smart_history_summary_empty(self):
        """Test smart summary for empty history."""
        history = ConversationHistory(user_id="test-user")
        summary = create_smart_history_summary(history)
        assert "No conversation history available" in summary

    def test_create_smart_history_summary_with_content(self):
        """Test smart summary for history with content."""
        history = ConversationHistory(
            user_id="test-user",
            history=[
                Message(role="user", content="I take ZOCLEAR medication"),
                Message(
                    role="assistant", content="I'll help you manage your medication"
                ),
            ],
        )
        summary = create_smart_history_summary(history)
        assert "Total messages: 2" in summary
        assert "Estimated tokens:" in summary
        assert "Token usage:" in summary


class TestSessionCreationDueToHistorySize:
    """Test session creation decisions based on history size."""

    def test_should_create_new_session_due_to_history_size_acceptable(self):
        """Test that session creation is not needed for acceptable history size."""
        history = ConversationHistory(
            user_id="test-user",
            history=[Message(role="user", content="Hello") for _ in range(10)],
        )
        should_create, reason = should_create_new_session_due_to_history_size(history)
        assert should_create is False
        assert "acceptable" in reason

    def test_should_create_new_session_due_to_history_size_too_large(self):
        """Test that session creation is needed for very large history."""
        history = ConversationHistory(
            user_id="test-user",
            history=[
                Message(role="user", content="Hello")
                for _ in range(HISTORY_MAX_MESSAGES * 3)
            ],
        )
        should_create, reason = should_create_new_session_due_to_history_size(history)
        assert should_create is True
        assert "too large" in reason

    def test_should_create_new_session_due_to_history_size_high_tokens(self):
        """Test that session creation is needed for high token usage."""
        # Create history with very long messages to exceed token limits
        # Need to create content that will definitely exceed 150% of the token limit
        # Since token estimation is len(text) // 4, we need content that's 6x the limit to get 150%
        long_content = "x" * (
            HISTORY_MAX_TOKENS * 6
        )  # 6x the token limit to ensure we exceed 150%
        history = ConversationHistory(
            user_id="test-user", history=[Message(role="user", content=long_content)]
        )
        should_create, reason = should_create_new_session_due_to_history_size(history)
        assert should_create is True
        assert "Token usage too high" in reason


class TestHistoryStateCleanup:
    """Test history state cleanup functionality."""

    def test_cleanup_history_state_no_temp_data(self):
        """Test cleanup when no temporary data exists."""
        history = ConversationHistory(
            user_id="test-user", state={"important": "data", "user_pref": "value"}
        )
        cleaned = cleanup_history_state(history)
        assert cleaned.state == {"important": "data", "user_pref": "value"}

    def test_cleanup_history_state_with_temp_data(self):
        """Test cleanup removes temporary data."""
        history = ConversationHistory(
            user_id="test-user",
            state={
                "important": "data",
                "temp_debug": "remove_me",
                "debug_info": "remove_me_too",
                "user_pref": "keep_me",
            },
        )
        cleaned = cleanup_history_state(history)
        assert "important" in cleaned.state
        assert "user_pref" in cleaned.state
        assert "temp_debug" not in cleaned.state
        assert "debug_info" not in cleaned.state


class TestHistoryManagementIntegration:
    """Test integration of history management functions."""

    def test_full_history_management_workflow(self):
        """Test complete history management workflow."""
        # Create a large history that exceeds message limit
        history = ConversationHistory(
            user_id="test-user",
            history=[
                Message(role="user", content=f"Message {i}") for i in range(120)
            ],  # Exceed HISTORY_MAX_MESSAGES * 2 (100)
        )

        # Analyze usage
        analysis = analyze_history_usage(history)
        assert analysis["message_count"] == 120
        assert analysis["should_truncate"] is True

        # Truncate for context
        truncated = truncate_history_for_context(history)
        assert len(truncated.history) < len(history.history)

        # Get optimized for agent
        agent_messages = get_optimized_history_for_agent(history)
        assert len(agent_messages) < 120

        # Check session creation decision
        should_create, reason = should_create_new_session_due_to_history_size(history)
        assert should_create is True

        # Create smart summary
        summary = create_smart_history_summary(history)
        assert "120" in summary  # Should mention the message count
