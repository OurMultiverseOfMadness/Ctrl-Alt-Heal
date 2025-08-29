"""Unit tests for session utilities."""

from datetime import datetime, UTC, timedelta
from unittest.mock import patch

from ctrl_alt_heal.utils.session_utils import (
    is_session_expired,
    get_session_inactivity_minutes,
    should_create_new_session,
    create_new_session,
    update_session_timestamp,
    add_message_to_session,
    get_session_duration_minutes,
    get_session_message_count,
    clear_session_history,
    is_session_active,
    get_session_summary,
    extend_session,
    get_session_status,
)
from ctrl_alt_heal.domain.models import ConversationHistory, Message
from ctrl_alt_heal.utils.constants import SESSION_TIMEOUT_MINUTES


class TestSessionExpiration:
    """Test session expiration functionality."""

    def test_session_not_expired_recent_activity(self):
        """Test that session is not expired with recent activity."""
        recent_time = datetime.now(UTC).isoformat()
        assert not is_session_expired(recent_time, 15)

    def test_session_expired_old_activity(self):
        """Test that session is expired with old activity."""
        old_time = (datetime.now(UTC) - timedelta(minutes=20)).isoformat()
        assert is_session_expired(old_time, 15)

    def test_session_expired_exact_timeout(self):
        """Test that session is expired at exact timeout."""
        timeout_time = (datetime.now(UTC) - timedelta(minutes=15)).isoformat()
        assert is_session_expired(timeout_time, 15)

    def test_session_not_expired_just_before_timeout(self):
        """Test that session is not expired just before timeout."""
        just_before_timeout = (
            datetime.now(UTC) - timedelta(minutes=14, seconds=59)
        ).isoformat()
        assert not is_session_expired(just_before_timeout, 15)

    def test_session_expired_invalid_timestamp(self):
        """Test that invalid timestamp is considered expired."""
        assert is_session_expired("invalid-timestamp", 15)

    def test_session_expired_none_timestamp(self):
        """Test that None timestamp is considered expired."""
        assert is_session_expired(None, 15)

    def test_session_expired_empty_string(self):
        """Test that empty string timestamp is considered expired."""
        assert is_session_expired("", 15)


class TestSessionInactivity:
    """Test session inactivity calculation."""

    def test_get_session_inactivity_minutes_recent(self):
        """Test inactivity calculation for recent activity."""
        recent_time = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
        inactivity = get_session_inactivity_minutes(recent_time)
        assert 4 <= inactivity <= 6  # Allow small time difference

    def test_get_session_inactivity_minutes_old(self):
        """Test inactivity calculation for old activity."""
        old_time = (datetime.now(UTC) - timedelta(minutes=30)).isoformat()
        inactivity = get_session_inactivity_minutes(old_time)
        assert 29 <= inactivity <= 31  # Allow small time difference

    def test_get_session_inactivity_minutes_invalid_timestamp(self):
        """Test inactivity calculation for invalid timestamp."""
        inactivity = get_session_inactivity_minutes("invalid-timestamp")
        assert inactivity == 999999

    def test_get_session_inactivity_minutes_none_timestamp(self):
        """Test inactivity calculation for None timestamp."""
        inactivity = get_session_inactivity_minutes(None)
        assert inactivity == 999999


class TestShouldCreateNewSession:
    """Test session creation decision logic."""

    def test_should_create_new_session_no_history(self):
        """Test that new session should be created when no history exists."""
        should_create, reason = should_create_new_session(None, 15)
        assert should_create
        assert "No existing session found" in reason

    def test_should_create_new_session_expired(self):
        """Test that new session should be created when existing session is expired."""
        old_time = (datetime.now(UTC) - timedelta(minutes=20)).isoformat()
        history = ConversationHistory(user_id="test-user", last_updated=old_time)
        should_create, reason = should_create_new_session(history, 15)
        assert should_create
        assert "Session expired due to" in reason
        assert "minutes of inactivity" in reason

    def test_should_not_create_new_session_active(self):
        """Test that new session should not be created when existing session is active."""
        recent_time = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
        history = ConversationHistory(user_id="test-user", last_updated=recent_time)
        should_create, reason = should_create_new_session(history, 15)
        assert not should_create
        assert "Session is still active" in reason

    def test_should_not_create_new_session_exact_timeout(self):
        """Test that new session should not be created at exact timeout boundary."""
        timeout_time = (datetime.now(UTC) - timedelta(minutes=15)).isoformat()
        history = ConversationHistory(user_id="test-user", last_updated=timeout_time)
        should_create, reason = should_create_new_session(history, 15)
        assert should_create  # Should be expired at exact timeout


class TestCreateNewSession:
    """Test new session creation."""

    def test_create_new_session(self):
        """Test creating a new session."""
        with patch("ctrl_alt_heal.utils.session_utils.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            session = create_new_session("test-user")

            assert session.user_id == "test-user"
            assert session.history == []
            assert session.last_updated == mock_now.isoformat()


class TestUpdateSessionTimestamp:
    """Test session timestamp updates."""

    def test_update_session_timestamp(self):
        """Test updating session timestamp."""
        old_time = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
        history = ConversationHistory(user_id="test-user", last_updated=old_time)

        with patch("ctrl_alt_heal.utils.session_utils.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            updated_history = update_session_timestamp(history)

            assert updated_history.last_updated == mock_now.isoformat()
            assert updated_history.user_id == "test-user"


class TestAddMessageToSession:
    """Test adding messages to session."""

    def test_add_message_to_session(self):
        """Test adding a message to session."""
        history = ConversationHistory(user_id="test-user")

        with patch("ctrl_alt_heal.utils.session_utils.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            updated_history = add_message_to_session(history, "user", "Hello")

            assert len(updated_history.history) == 1
            assert updated_history.history[0].role == "user"
            assert updated_history.history[0].content == "Hello"
            assert updated_history.last_updated == mock_now.isoformat()

    def test_add_multiple_messages_to_session(self):
        """Test adding multiple messages to session."""
        history = ConversationHistory(user_id="test-user")

        with patch("ctrl_alt_heal.utils.session_utils.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            history = add_message_to_session(history, "user", "Hello")
            history = add_message_to_session(history, "assistant", "Hi there!")

            assert len(history.history) == 2
            assert history.history[0].role == "user"
            assert history.history[0].content == "Hello"
            assert history.history[1].role == "assistant"
            assert history.history[1].content == "Hi there!"


class TestSessionDuration:
    """Test session duration calculation."""

    def test_get_session_duration_minutes_with_messages(self):
        """Test duration calculation with messages."""
        end_time = datetime(2024, 1, 1, 12, 15, 0, tzinfo=UTC)

        history = ConversationHistory(
            user_id="test-user", last_updated=end_time.isoformat()
        )
        history.history = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi"),
            Message(role="user", content="How are you?"),
        ]

        duration = get_session_duration_minutes(history)
        # Duration should be estimated based on number of messages (3 messages = 3 minutes)
        assert duration == 3

    def test_get_session_duration_minutes_no_messages(self):
        """Test duration calculation with no messages."""
        history = ConversationHistory(user_id="test-user")
        duration = get_session_duration_minutes(history)
        assert duration == 0

    def test_get_session_duration_minutes_invalid_timestamp(self):
        """Test duration calculation with invalid timestamp."""
        history = ConversationHistory(
            user_id="test-user", last_updated="invalid-timestamp"
        )
        history.history = [Message(role="user", content="Hello")]

        duration = get_session_duration_minutes(history)
        assert duration == 0


class TestSessionMessageCount:
    """Test session message counting."""

    def test_get_session_message_count_empty(self):
        """Test message count for empty session."""
        history = ConversationHistory(user_id="test-user")
        count = get_session_message_count(history)
        assert count == 0

    def test_get_session_message_count_with_messages(self):
        """Test message count with messages."""
        history = ConversationHistory(user_id="test-user")
        history.history = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi"),
            Message(role="user", content="How are you?"),
        ]
        count = get_session_message_count(history)
        assert count == 3


class TestClearSessionHistory:
    """Test clearing session history."""

    def test_clear_session_history(self):
        """Test clearing session history."""
        history = ConversationHistory(user_id="test-user")
        history.history = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi"),
        ]

        with patch("ctrl_alt_heal.utils.session_utils.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            cleared_history = clear_session_history(history)

            assert len(cleared_history.history) == 0
            assert cleared_history.last_updated == mock_now.isoformat()
            assert cleared_history.user_id == "test-user"


class TestSessionActive:
    """Test session active status."""

    def test_is_session_active_recent(self):
        """Test that session is active with recent activity."""
        recent_time = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
        history = ConversationHistory(user_id="test-user", last_updated=recent_time)
        assert is_session_active(history, 15)

    def test_is_session_active_expired(self):
        """Test that session is not active when expired."""
        old_time = (datetime.now(UTC) - timedelta(minutes=20)).isoformat()
        history = ConversationHistory(user_id="test-user", last_updated=old_time)
        assert not is_session_active(history, 15)

    def test_is_session_active_exact_timeout(self):
        """Test that session is not active at exact timeout."""
        timeout_time = (datetime.now(UTC) - timedelta(minutes=15)).isoformat()
        history = ConversationHistory(user_id="test-user", last_updated=timeout_time)
        assert not is_session_active(history, 15)


class TestSessionSummary:
    """Test session summary generation."""

    def test_get_session_summary_empty_session(self):
        """Test summary for empty session."""
        history = ConversationHistory(user_id="test-user")
        summary = get_session_summary(history)

        assert summary["user_id"] == "test-user"
        assert summary["message_count"] == 0
        assert summary["duration_minutes"] == 0
        assert "inactivity_minutes" in summary
        assert summary["is_active"] is True
        assert summary["timeout_minutes"] == SESSION_TIMEOUT_MINUTES
        assert "will_expire_in_minutes" in summary

    def test_get_session_summary_with_messages(self):
        """Test summary for session with messages."""
        # Use a recent time to ensure session is active
        end_time = datetime.now(UTC) - timedelta(minutes=5)

        history = ConversationHistory(
            user_id="test-user", last_updated=end_time.isoformat()
        )
        history.history = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi"),
        ]

        summary = get_session_summary(history)

        assert summary["user_id"] == "test-user"
        assert summary["message_count"] == 2
        assert (
            summary["duration_minutes"] == 2
        )  # 2 messages = 2 minutes estimated duration
        assert summary["is_active"] is True
        assert summary["timeout_minutes"] == SESSION_TIMEOUT_MINUTES


class TestExtendSession:
    """Test session extension."""

    def test_extend_session(self):
        """Test extending session timeout."""
        old_time = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
        history = ConversationHistory(user_id="test-user", last_updated=old_time)

        with patch("ctrl_alt_heal.utils.session_utils.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            extended_history = extend_session(history)

            assert extended_history.last_updated == mock_now.isoformat()
            assert extended_history.user_id == "test-user"


class TestSessionStatus:
    """Test session status checking."""

    def test_get_session_status_no_session(self):
        """Test status when no session exists."""
        status = get_session_status(None)

        assert status["exists"] is False
        assert status["is_active"] is False
        assert "No session exists" in status["reason"]

    def test_get_session_status_active_session(self):
        """Test status for active session."""
        recent_time = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
        history = ConversationHistory(user_id="test-user", last_updated=recent_time)

        status = get_session_status(history)

        assert status["exists"] is True
        assert status["is_active"] is True
        assert "Session active" in status["reason"]
        assert "inactivity_minutes" in status
        assert "timeout_minutes" in status
        assert "will_expire_in_minutes" in status

    def test_get_session_status_expired_session(self):
        """Test status for expired session."""
        old_time = (datetime.now(UTC) - timedelta(minutes=20)).isoformat()
        history = ConversationHistory(user_id="test-user", last_updated=old_time)

        status = get_session_status(history)

        assert status["exists"] is True
        assert status["is_active"] is False
        assert "Session expired" in status["reason"]
        assert "minutes of inactivity" in status["reason"]


class TestSessionConstants:
    """Test session constants integration."""

    def test_default_timeout_uses_constant(self):
        """Test that default timeout uses the constant value."""
        # This test ensures we're using the constant from constants.py
        assert SESSION_TIMEOUT_MINUTES == 15

    def test_session_expired_uses_default_timeout(self):
        """Test that session expiration uses default timeout."""
        # Test with exact timeout boundary
        timeout_time = (datetime.now(UTC) - timedelta(minutes=15)).isoformat()
        assert is_session_expired(timeout_time)  # Uses default timeout

        # Test with just before timeout
        just_before_timeout = (
            datetime.now(UTC) - timedelta(minutes=14, seconds=59)
        ).isoformat()
        assert not is_session_expired(just_before_timeout)  # Uses default timeout
