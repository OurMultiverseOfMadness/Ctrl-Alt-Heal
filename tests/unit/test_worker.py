"""Tests for the worker module functionality."""

import json
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from pytz import UTC

from ctrl_alt_heal.worker import (
    process_agent_response,
    handle_text_message,
    handle_photo_message,
    handler,
)
from ctrl_alt_heal.domain.models import User, ConversationHistory


class TestProcessAgentResponse:
    """Test the process_agent_response function."""

    def test_process_agent_response_with_tool_calls(self):
        """Test processing agent response with tool calls."""
        # Arrange
        agent_response = {
            "tool_calls": [
                {
                    "name": "get_user_profile",
                    "args": {"user_id": "test-user"},
                    "tool_call_id": "call-1",
                }
            ]
        }
        agent = Mock()
        agent.return_value = "Final response"
        user = User(
            user_id="test-user",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        history = ConversationHistory(user_id="test-user")
        chat_id = "12345"

        with patch("ctrl_alt_heal.worker.tool_registry") as mock_registry, patch(
            "ctrl_alt_heal.infrastructure.history_store.boto3"
        ) as mock_boto3:
            mock_registry.get.return_value = Mock(return_value={"status": "success"})
            mock_boto3.resource.return_value = Mock()

            # Act
            process_agent_response(agent_response, agent, user, history, chat_id)

            # Assert
            agent.assert_called_once()
            mock_registry.get.assert_called_once_with("get_user_profile")

    def test_process_agent_response_final_message(self):
        """Test processing agent response with final message."""
        # Arrange
        agent_response = "This is the final response"
        agent = Mock()
        user = User(
            user_id="test-user",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        history = ConversationHistory(user_id="test-user")
        chat_id = "12345"

        with patch(
            "ctrl_alt_heal.worker.send_telegram_message_with_retry"
        ) as mock_send, patch(
            "ctrl_alt_heal.infrastructure.history_store.boto3"
        ) as mock_boto3:
            mock_boto3.resource.return_value = Mock()
            # Act
            process_agent_response(agent_response, agent, user, history, chat_id)

            # Assert
            mock_send.assert_called_once_with(
                chat_id, "This is the final response", max_retries=3
            )
            assert len(history.history) == 1
            assert history.history[0].role == "assistant"
            assert history.history[0].content == "This is the final response"

    def test_process_agent_response_cleans_xml_tags(self):
        """Test that XML-like tags are cleaned from responses."""
        # Arrange
        agent_response = "<thinking>I should respond</thinking>Here is the answer<response>Final answer</response>"
        agent = Mock()
        user = User(
            user_id="test-user",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        history = ConversationHistory(user_id="test-user")
        chat_id = "12345"

        with patch(
            "ctrl_alt_heal.worker.send_telegram_message_with_retry"
        ) as mock_send, patch(
            "ctrl_alt_heal.infrastructure.history_store.boto3"
        ) as mock_boto3:
            mock_boto3.resource.return_value = Mock()
            # Act
            process_agent_response(agent_response, agent, user, history, chat_id)

            # Assert
            mock_send.assert_called_once_with(
                chat_id, "Here is the answerFinal answer", max_retries=3
            )
            assert history.history[0].content == "Here is the answerFinal answer"

    def test_process_agent_response_empty_after_cleaning(self):
        """Test handling of empty response after cleaning."""
        # Arrange
        agent_response = "<thinking>Only thinking content</thinking>"
        agent = Mock()
        user = User(
            user_id="test-user",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        history = ConversationHistory(user_id="test-user")
        chat_id = "12345"

        with patch(
            "ctrl_alt_heal.worker.send_telegram_message_with_retry"
        ) as mock_send, patch(
            "ctrl_alt_heal.infrastructure.history_store.boto3"
        ) as mock_boto3:
            mock_boto3.resource.return_value = Mock()
            # Act
            process_agent_response(agent_response, agent, user, history, chat_id)

            # Assert
            expected_message = "I apologize, but I couldn't generate a proper response. Please try asking your question again."
            mock_send.assert_called_once_with(chat_id, expected_message, max_retries=3)


class TestHandleTextMessage:
    """Test the handle_text_message function."""

    def test_handle_text_message_creates_agent_and_processes(self):
        """Test that text message handling creates agent and processes response."""
        # Arrange
        message = {"text": "Hello, how are you?"}
        chat_id = "12345"
        user = User(
            user_id="test-user",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        history = ConversationHistory(user_id="test-user")

        with patch("ctrl_alt_heal.worker.get_agent") as mock_get_agent, patch(
            "ctrl_alt_heal.worker.process_agent_response"
        ) as mock_process:
            mock_agent = Mock()
            mock_agent.return_value = "Agent response"
            mock_get_agent.return_value = mock_agent

            # Act
            handle_text_message(message, chat_id, user, history)

            # Assert
            mock_get_agent.assert_called_once_with(user, history)
            mock_agent.assert_called_once()
            mock_process.assert_called_once_with(
                "Agent response", mock_agent, user, history, chat_id
            )
            assert len(history.history) == 1
            assert history.history[0].role == "user"
            assert history.history[0].content == "Hello, how are you?"


class TestHandlePhotoMessage:
    """Test the handle_photo_message function."""

    def test_handle_photo_message_uploads_and_processes(self):
        """Test that photo message handling uploads to S3 and processes."""
        # Arrange
        message = {"photo": [{"file_id": "photo-123", "file_size": 1000}]}
        chat_id = "12345"
        user = User(
            user_id="test-user",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        history = ConversationHistory(user_id="test-user")

        with patch(
            "ctrl_alt_heal.worker.get_telegram_file_path"
        ) as mock_get_path, patch(
            "ctrl_alt_heal.worker.get_secret"
        ) as mock_get_secret, patch(
            "ctrl_alt_heal.worker.requests.get"
        ) as mock_requests_get, patch(
            "ctrl_alt_heal.worker.s3_client.put_object"
        ) as mock_s3_put, patch(
            "ctrl_alt_heal.worker.get_agent"
        ) as mock_get_agent, patch(
            "ctrl_alt_heal.worker.process_agent_response"
        ) as mock_process:
            mock_get_path.return_value = "photos/file.jpg"
            mock_get_secret.return_value = {"value": "bot-token"}
            mock_requests_get.return_value.status_code = 200
            mock_requests_get.return_value.content = b"image-data"

            mock_agent = Mock()
            mock_agent.return_value = "Agent response"
            mock_get_agent.return_value = mock_agent

            # Act
            handle_photo_message(message, chat_id, user, history)

            # Assert
            mock_s3_put.assert_called_once()
            mock_get_agent.assert_called_once()
            mock_process.assert_called_once()
            assert len(history.history) == 1
            assert "image" in history.history[0].content.lower()

    def test_handle_photo_message_file_download_failure(self):
        """Test handling when file download fails."""
        # Arrange
        message = {"photo": [{"file_id": "photo-123", "file_size": 1000}]}
        chat_id = "12345"
        user = User(
            user_id="test-user",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        history = ConversationHistory(user_id="test-user")

        with patch(
            "ctrl_alt_heal.worker.get_telegram_file_path"
        ) as mock_get_path, patch(
            "ctrl_alt_heal.worker.get_secret"
        ) as mock_get_secret, patch(
            "ctrl_alt_heal.worker.requests.get"
        ) as mock_requests_get, patch(
            "ctrl_alt_heal.worker.send_telegram_message_with_retry"
        ) as mock_send:
            mock_get_path.return_value = "photos/file.jpg"
            mock_get_secret.return_value = {"value": "bot-token"}
            mock_requests_get.return_value.status_code = 404

            # Act
            handle_photo_message(message, chat_id, user, history)

            # Assert
            mock_send.assert_called_once_with(
                chat_id,
                "Sorry, I had trouble downloading the image. Please try again.",
                max_retries=2,
            )


class TestHandler:
    """Test the main handler function."""

    def test_handler_creates_new_user(self):
        """Test handler creates new user when none exists."""
        # Arrange
        event = {
            "Records": [
                {
                    "body": json.dumps(
                        {
                            "message": {
                                "chat": {
                                    "id": 12345,
                                    "first_name": "Test",
                                    "last_name": "User",
                                },
                                "from": {
                                    "id": 12345,
                                    "first_name": "Test",
                                    "last_name": "User",
                                },
                                "text": "Hello",
                            }
                        }
                    )
                }
            ]
        }

        with patch(
            "ctrl_alt_heal.worker.IdentitiesStore"
        ) as mock_identities_store, patch(
            "ctrl_alt_heal.worker.UsersStore"
        ) as mock_users_store, patch(
            "ctrl_alt_heal.worker.HistoryStore"
        ) as mock_history_store, patch(
            "ctrl_alt_heal.worker.handle_text_message"
        ) as mock_handle_text:
            mock_identities_instance = Mock()
            mock_identities_instance.find_user_id_by_identity.return_value = None
            mock_identities_store.return_value = mock_identities_instance

            mock_users_instance = Mock()
            mock_users_store.return_value = mock_users_instance

            mock_history_instance = Mock()
            mock_history_instance.get_latest_history.return_value = None
            mock_history_store.return_value = mock_history_instance

            # Act
            handler(event, {})

            # Assert
            mock_users_instance.upsert_user.assert_called_once()
            mock_identities_instance.link_identity.assert_called_once()
            mock_handle_text.assert_called_once()

    def test_handler_updates_existing_user(self):
        """Test handler updates existing user."""
        # Arrange
        event = {
            "Records": [
                {
                    "body": json.dumps(
                        {
                            "message": {
                                "chat": {
                                    "id": 12345,
                                    "first_name": "Updated",
                                    "last_name": "Name",
                                },
                                "from": {
                                    "id": 12345,
                                    "first_name": "Updated",
                                    "last_name": "Name",
                                },
                                "text": "Hello",
                            }
                        }
                    )
                }
            ]
        }

        existing_user = User(
            user_id="existing-user",
            first_name="Old",
            last_name="Name",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

        with patch(
            "ctrl_alt_heal.worker.IdentitiesStore"
        ) as mock_identities_store, patch(
            "ctrl_alt_heal.worker.UsersStore"
        ) as mock_users_store, patch(
            "ctrl_alt_heal.worker.HistoryStore"
        ) as mock_history_store, patch(
            "ctrl_alt_heal.worker.handle_text_message"
        ) as mock_handle_text:  # noqa: F841
            mock_identities_instance = Mock()
            mock_identities_instance.find_user_id_by_identity.return_value = (
                "existing-user"
            )
            mock_identities_store.return_value = mock_identities_instance

            mock_users_instance = Mock()
            mock_users_instance.get_user.return_value = existing_user
            mock_users_store.return_value = mock_users_instance

            mock_history_instance = Mock()
            mock_history_instance.get_latest_history.return_value = None
            mock_history_store.return_value = mock_history_instance

            # Act
            handler(event, {})

            # Assert
            mock_users_instance.upsert_user.assert_called_once()
            # Verify the user was updated with new name
            updated_user = mock_users_instance.upsert_user.call_args[0][0]
            assert updated_user.first_name == "Updated"
            assert updated_user.last_name == "Name"

    def test_handler_session_timeout_creates_new_session(self):
        """Test handler creates new session when existing session times out due to inactivity."""
        # Arrange
        event = {
            "Records": [
                {
                    "body": json.dumps(
                        {
                            "message": {
                                "chat": {"id": 12345, "first_name": "Test"},
                                "from": {"id": 12345, "first_name": "Test"},
                                "text": "Hello",
                            }
                        }
                    )
                }
            ]
        }

        existing_user = User(
            user_id="test-user",
            first_name="Test",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

        old_history = ConversationHistory(
            user_id="test-user",
            last_updated=(
                datetime.now(UTC) - timedelta(minutes=20)
            ).isoformat(),  # 20 minutes of inactivity
        )

        with patch(
            "ctrl_alt_heal.worker.IdentitiesStore"
        ) as mock_identities_store, patch(
            "ctrl_alt_heal.worker.UsersStore"
        ) as mock_users_store, patch(
            "ctrl_alt_heal.worker.HistoryStore"
        ) as mock_history_store, patch(
            "ctrl_alt_heal.worker.handle_text_message"
        ) as mock_handle_text, patch(
            "ctrl_alt_heal.worker.should_create_new_session"
        ) as mock_should_create, patch(
            "ctrl_alt_heal.worker.create_new_session"
        ) as mock_create_new, patch(
            "ctrl_alt_heal.worker.update_session_timestamp"
        ) as mock_update_timestamp:  # noqa: F841
            mock_identities_instance = Mock()
            mock_identities_instance.find_user_id_by_identity.return_value = "test-user"
            mock_identities_store.return_value = mock_identities_instance

            mock_users_instance = Mock()
            mock_users_instance.get_user.return_value = existing_user
            mock_users_store.return_value = mock_users_instance

            mock_history_instance = Mock()
            mock_history_instance.get_latest_history.return_value = old_history
            mock_history_store.return_value = mock_history_instance

            # Mock session management functions
            mock_should_create.return_value = (
                True,
                "Session expired due to 20 minutes of inactivity",
            )
            new_session = ConversationHistory(user_id="test-user")
            mock_create_new.return_value = new_session

            # Act
            handler(event, {})

            # Assert
            mock_should_create.assert_called_once_with(
                old_history, 15
            )  # 15 minute timeout
            mock_create_new.assert_called_once_with("test-user")
            mock_handle_text.assert_called_once()
            # Verify that the new session was passed to handle_text_message
            call_args = mock_handle_text.call_args[0]
            session_arg = call_args[3]  # history parameter
            assert session_arg.user_id == "test-user"

    def test_handler_continues_active_session(self):
        """Test handler continues existing session when it's still active."""
        # Arrange
        event = {
            "Records": [
                {
                    "body": json.dumps(
                        {
                            "message": {
                                "chat": {"id": 12345, "first_name": "Test"},
                                "from": {"id": 12345, "first_name": "Test"},
                                "text": "Hello",
                            }
                        }
                    )
                }
            ]
        }

        existing_user = User(
            user_id="test-user",
            first_name="Test",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

        active_history = ConversationHistory(
            user_id="test-user",
            last_updated=(
                datetime.now(UTC) - timedelta(minutes=5)
            ).isoformat(),  # 5 minutes of inactivity
        )

        with patch(
            "ctrl_alt_heal.worker.IdentitiesStore"
        ) as mock_identities_store, patch(
            "ctrl_alt_heal.worker.UsersStore"
        ) as mock_users_store, patch(
            "ctrl_alt_heal.worker.HistoryStore"
        ) as mock_history_store, patch(
            "ctrl_alt_heal.worker.handle_text_message"
        ) as mock_handle_text, patch(
            "ctrl_alt_heal.worker.should_create_new_session"
        ) as mock_should_create, patch(
            "ctrl_alt_heal.worker.create_new_session"
        ) as mock_create_new, patch(
            "ctrl_alt_heal.worker.update_session_timestamp"
        ) as mock_update_timestamp:
            mock_identities_instance = Mock()
            mock_identities_instance.find_user_id_by_identity.return_value = "test-user"
            mock_identities_store.return_value = mock_identities_instance

            mock_users_instance = Mock()
            mock_users_instance.get_user.return_value = existing_user
            mock_users_store.return_value = mock_users_instance

            mock_history_instance = Mock()
            mock_history_instance.get_latest_history.return_value = active_history
            mock_history_store.return_value = mock_history_instance

            # Mock session management functions
            mock_should_create.return_value = (False, "Session is still active")
            updated_history = ConversationHistory(user_id="test-user")
            mock_update_timestamp.return_value = updated_history

            # Act
            handler(event, {})

            # Assert
            mock_should_create.assert_called_once_with(
                active_history, 15
            )  # 15 minute timeout
            mock_update_timestamp.assert_called_once_with(active_history)
            mock_create_new.assert_not_called()  # Should not create new session
            mock_handle_text.assert_called_once()
            # Verify that the updated session was passed to handle_text_message
            call_args = mock_handle_text.call_args[0]
            session_arg = call_args[3]  # history parameter
            assert session_arg.user_id == "test-user"
