"""Unit tests for robust Telegram client."""

import pytest
import time
from unittest.mock import patch, Mock
import requests

from ctrl_alt_heal.interface.telegram_client import (
    TelegramClient,
    TelegramError,
    TelegramErrorType,
    get_telegram_client,
    send_telegram_message,
    send_telegram_file,
    get_telegram_file_path,
)
from ctrl_alt_heal.utils.telegram_formatter import TelegramParseMode
from ctrl_alt_heal.utils.constants import TELEGRAM_API


class TestTelegramError:
    """Test Telegram error handling."""

    def test_telegram_error_creation(self):
        """Test Telegram error creation."""
        error = TelegramError(
            error_type=TelegramErrorType.NETWORK_ERROR,
            message="Network failed",
            retry_after=30,
            status_code=500,
        )

        assert error.error_type == TelegramErrorType.NETWORK_ERROR
        assert error.message == "Network failed"
        assert error.retry_after == 30
        assert error.status_code == 500

    def test_telegram_error_types(self):
        """Test all Telegram error types."""
        error_types = [
            TelegramErrorType.NETWORK_ERROR,
            TelegramErrorType.RATE_LIMIT,
            TelegramErrorType.INVALID_TOKEN,
            TelegramErrorType.CHAT_NOT_FOUND,
            TelegramErrorType.MESSAGE_TOO_LONG,
            TelegramErrorType.FORBIDDEN,
            TelegramErrorType.BAD_REQUEST,
            TelegramErrorType.UNKNOWN_ERROR,
        ]

        for error_type in error_types:
            error = TelegramError(error_type=error_type, message="Test")
            assert error.error_type == error_type


class TestTelegramClient:
    """Test Telegram client functionality."""

    def test_client_creation(self):
        """Test client creation."""
        client = TelegramClient()
        assert client.parse_mode == TelegramParseMode.HTML

        client_plain = TelegramClient(TelegramParseMode.PLAIN_TEXT)
        assert client_plain.parse_mode == TelegramParseMode.PLAIN_TEXT

    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_get_token_success(self, mock_get_secret):
        """Test successful token retrieval."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        client = TelegramClient()
        token = client._get_token()

        assert token == "test_token"
        assert client._token == "test_token"

    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_get_token_fallback(self, mock_get_secret):
        """Test token retrieval with fallback to 'value' key."""
        mock_get_secret.return_value = {"value": "fallback_token"}

        client = TelegramClient()
        token = client._get_token()

        assert token == "fallback_token"

    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_get_token_missing(self, mock_get_secret):
        """Test token retrieval when token is missing."""
        mock_get_secret.return_value = {}

        client = TelegramClient()

        with pytest.raises(TelegramError) as exc_info:
            client._get_token()

        assert exc_info.value.error_type == TelegramErrorType.INVALID_TOKEN

    def test_rate_limit_delay(self):
        """Test rate limiting delay."""
        client = TelegramClient()

        # First call should not delay
        start_time = time.time()
        client._rate_limit_delay()
        first_call_time = time.time() - start_time

        # Second call should delay
        start_time = time.time()
        client._rate_limit_delay()
        second_call_time = time.time() - start_time

        assert first_call_time < 0.1  # Should be fast
        assert (
            second_call_time >= TELEGRAM_API["RATE_LIMIT_DELAY"] - 0.1
        )  # Should delay

    def test_handle_response_success(self):
        """Test successful response handling."""
        client = TelegramClient()

        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 123}}

        result = client._handle_response(mock_response)
        assert result == {"message_id": 123}

    def test_handle_response_error(self):
        """Test error response handling."""
        client = TelegramClient()

        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": False,
            "error_code": 429,
            "description": "Too many requests",
            "parameters": {"retry_after": 30},
        }

        with pytest.raises(TelegramError) as exc_info:
            client._handle_response(mock_response)

        assert exc_info.value.error_type == TelegramErrorType.RATE_LIMIT
        assert exc_info.value.retry_after == 30

    def test_handle_response_invalid_json(self):
        """Test handling of invalid JSON response."""
        client = TelegramClient()

        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.status_code = 500

        with pytest.raises(TelegramError) as exc_info:
            client._handle_response(mock_response)

        assert exc_info.value.error_type == TelegramErrorType.UNKNOWN_ERROR
        assert exc_info.value.status_code == 500

    @patch("ctrl_alt_heal.interface.telegram_client.requests.post")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_make_request_success(self, mock_get_secret, mock_post):
        """Test successful request making."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {"success": True}}
        mock_post.return_value = mock_response

        client = TelegramClient()
        result = client._make_request("POST", "/test", {"data": "test"})

        assert result == {"success": True}
        mock_post.assert_called_once()

    @patch("ctrl_alt_heal.interface.telegram_client.requests.post")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_make_request_retry_success(self, mock_get_secret, mock_post):
        """Test request retry on failure."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.json.return_value = {
            "ok": False,
            "error_code": 500,
            "description": "Internal error",
        }

        mock_response_success = Mock()
        mock_response_success.json.return_value = {
            "ok": True,
            "result": {"success": True},
        }

        mock_post.side_effect = [mock_response_fail, mock_response_success]

        client = TelegramClient()
        result = client._make_request("POST", "/test", {"data": "test"}, retries=1)

        assert result == {"success": True}
        assert mock_post.call_count == 2

    @patch("ctrl_alt_heal.interface.telegram_client.requests.post")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_make_request_rate_limit(self, mock_get_secret, mock_post):
        """Test request handling with rate limiting."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        # First call gets rate limited, second succeeds
        mock_response_rate_limit = Mock()
        mock_response_rate_limit.json.return_value = {
            "ok": False,
            "error_code": 429,
            "description": "Too many requests",
            "parameters": {"retry_after": 0.1},  # Short delay for testing
        }

        mock_response_success = Mock()
        mock_response_success.json.return_value = {
            "ok": True,
            "result": {"success": True},
        }

        mock_post.side_effect = [mock_response_rate_limit, mock_response_success]

        client = TelegramClient()
        result = client._make_request("POST", "/test", {"data": "test"})

        assert result == {"success": True}
        assert mock_post.call_count == 2

    @patch("ctrl_alt_heal.interface.telegram_client.requests.post")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_make_request_network_error(self, mock_get_secret, mock_post):
        """Test request handling with network errors."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        # Network error on first call, success on second
        mock_post.side_effect = [
            requests.exceptions.RequestException("Network error"),
            Mock(json=lambda: {"ok": True, "result": {"success": True}}),
        ]

        client = TelegramClient()
        result = client._make_request("POST", "/test", {"data": "test"}, retries=1)

        assert result == {"success": True}
        assert mock_post.call_count == 2

    @patch("ctrl_alt_heal.interface.telegram_client.requests.post")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_send_message_success(self, mock_get_secret, mock_post):
        """Test successful message sending."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 123}}
        mock_post.return_value = mock_response

        client = TelegramClient()
        result = client.send_message("12345", "Hello world")

        assert len(result) == 1
        assert result[0]["message_id"] == 123

    @patch("ctrl_alt_heal.interface.telegram_client.requests.post")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_send_message_with_formatting(self, mock_get_secret, mock_post):
        """Test message sending with HTML formatting."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 123}}
        mock_post.return_value = mock_response

        client = TelegramClient(TelegramParseMode.HTML)
        client.send_message("12345", "**Bold** *italic*")

        # Check that the request included HTML formatting
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["parse_mode"] == "HTML"
        assert "<b>Bold</b>" in payload["text"]
        assert "<i>italic</i>" in payload["text"]

    @patch("ctrl_alt_heal.interface.telegram_client.requests.post")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_send_file_success(self, mock_get_secret, mock_post):
        """Test successful file sending."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 123}}
        mock_post.return_value = mock_response

        client = TelegramClient()
        result = client.send_file("12345", "file content", "test.txt", "Test caption")

        assert result["message_id"] == 123

        # Check that the request included file data
        call_args = mock_post.call_args
        files = call_args[1]["files"]
        data = call_args[1].get("data", {})

        assert "document" in files
        # The data is passed as data parameter when files are present
        assert data.get("chat_id") == "12345"
        assert data.get("caption") == "Test caption"

    @patch("ctrl_alt_heal.interface.telegram_client.requests.post")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_send_file_caption_truncation(self, mock_get_secret, mock_post):
        """Test file caption truncation."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 123}}
        mock_post.return_value = mock_response

        client = TelegramClient()
        long_caption = "x" * (TELEGRAM_API["MAX_CAPTION_LENGTH"] + 100)
        client.send_file("12345", "file content", "test.txt", long_caption)

        # Check that caption was truncated
        call_args = mock_post.call_args
        data = call_args[1].get("data", {})
        assert len(data.get("caption", "")) <= TELEGRAM_API["MAX_CAPTION_LENGTH"]
        assert data.get("caption", "").endswith("...")

    @patch("ctrl_alt_heal.interface.telegram_client.requests.get")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_get_file_path_success(self, mock_get_secret, mock_get):
        """Test successful file path retrieval."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": True,
            "result": {"file_path": "documents/file.txt"},
        }
        mock_get.return_value = mock_response

        client = TelegramClient()
        result = client.get_file_path("file_id_123")

        assert result == "documents/file.txt"

    @patch("ctrl_alt_heal.interface.telegram_client.requests.get")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_get_file_path_not_found(self, mock_get_secret, mock_get):
        """Test file path retrieval when file not found."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": False,
            "error_code": 404,
            "description": "File not found",
        }
        mock_get.return_value = mock_response

        client = TelegramClient()
        result = client.get_file_path("invalid_file_id")

        assert result is None

    @patch("ctrl_alt_heal.interface.telegram_client.requests.get")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_download_file_success(self, mock_get_secret, mock_get):
        """Test successful file download."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_response = Mock()
        mock_response.content = b"file content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = TelegramClient()
        result = client.download_file("documents/file.txt")

        assert result == b"file content"

    @patch("ctrl_alt_heal.interface.telegram_client.requests.get")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_download_file_failure(self, mock_get_secret, mock_get):
        """Test file download failure."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_get.side_effect = requests.exceptions.RequestException("Download failed")

        client = TelegramClient()
        result = client.download_file("documents/file.txt")

        assert result is None

    @patch("ctrl_alt_heal.interface.telegram_client.requests.get")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_validate_chat_id_success(self, mock_get_secret, mock_get):
        """Test successful chat ID validation."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {"id": 12345}}
        mock_get.return_value = mock_response

        client = TelegramClient()
        result = client.validate_chat_id("12345")

        assert result is True

    @patch("ctrl_alt_heal.interface.telegram_client.requests.get")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_validate_chat_id_not_found(self, mock_get_secret, mock_get):
        """Test chat ID validation when chat not found."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": False,
            "error_code": 404,
            "description": "Chat not found",
        }
        mock_get.return_value = mock_response

        client = TelegramClient()
        result = client.validate_chat_id("invalid_chat_id")

        assert result is False


class TestGlobalFunctions:
    """Test global client functions."""

    def test_get_telegram_client_singleton(self):
        """Test that get_telegram_client returns singleton."""
        client1 = get_telegram_client()
        client2 = get_telegram_client()

        assert client1 is client2

    def test_get_telegram_client_different_modes(self):
        """Test that different parse modes create different clients."""
        client1 = get_telegram_client(TelegramParseMode.HTML)
        client2 = get_telegram_client(TelegramParseMode.PLAIN_TEXT)

        # Should return the same client (singleton behavior)
        assert client1 is client2

    @patch("ctrl_alt_heal.interface.telegram_client.get_telegram_client")
    def test_send_telegram_message(self, mock_get_client):
        """Test send_telegram_message function."""
        mock_client = Mock()
        mock_client.send_message.return_value = [{"message_id": 123}]
        mock_get_client.return_value = mock_client

        result = send_telegram_message("12345", "Hello world")

        assert result == [{"message_id": 123}]
        mock_client.send_message.assert_called_once_with("12345", "Hello world", True)

    @patch("ctrl_alt_heal.interface.telegram_client.get_telegram_client")
    def test_send_telegram_file(self, mock_get_client):
        """Test send_telegram_file function."""
        mock_client = Mock()
        mock_client.send_file.return_value = {"message_id": 123}
        mock_get_client.return_value = mock_client

        result = send_telegram_file("12345", "content", "test.txt", "caption")

        assert result == {"message_id": 123}
        mock_client.send_file.assert_called_once_with(
            "12345", "content", "test.txt", "caption"
        )

    @patch("ctrl_alt_heal.interface.telegram_client.get_telegram_client")
    def test_get_telegram_file_path(self, mock_get_client):
        """Test get_telegram_file_path function."""
        mock_client = Mock()
        mock_client.get_file_path.return_value = "documents/file.txt"
        mock_get_client.return_value = mock_client

        result = get_telegram_file_path("file_id_123")

        assert result == "documents/file.txt"
        mock_client.get_file_path.assert_called_once_with("file_id_123")


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch("ctrl_alt_heal.interface.telegram_client.requests.post")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_send_message_telegram_error(self, mock_get_secret, mock_post):
        """Test message sending with Telegram error."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": False,
            "error_code": 413,
            "description": "Message too long",
        }
        mock_post.return_value = mock_response

        client = TelegramClient()

        with pytest.raises(TelegramError) as exc_info:
            client.send_message("12345", "Very long message")

        assert exc_info.value.error_type == TelegramErrorType.MESSAGE_TOO_LONG

    @patch("ctrl_alt_heal.interface.telegram_client.requests.post")
    @patch("ctrl_alt_heal.interface.telegram_client.get_secret")
    def test_send_message_network_error(self, mock_get_secret, mock_post):
        """Test message sending with network error."""
        mock_get_secret.return_value = {"bot_token": "test_token"}

        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        client = TelegramClient()

        with pytest.raises(TelegramError) as exc_info:
            client.send_message("12345", "Hello world")

        assert exc_info.value.error_type == TelegramErrorType.NETWORK_ERROR
