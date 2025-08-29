"""Robust Telegram client with retry logic, rate limiting, and error handling."""

from __future__ import annotations

import logging
import time
import requests
from typing import Dict, Any, Optional, List, Union
from enum import Enum

from ctrl_alt_heal.infrastructure.secrets import get_secret
from ctrl_alt_heal.config import settings
from ctrl_alt_heal.utils.constants import TELEGRAM_API
from ctrl_alt_heal.utils.telegram_formatter import (
    TelegramMessageBuilder,
    TelegramParseMode,
)

logger = logging.getLogger(__name__)


class TelegramErrorType(Enum):
    """Types of Telegram API errors."""

    NETWORK_ERROR = "network_error"
    RATE_LIMIT = "rate_limit"
    INVALID_TOKEN = "invalid_token"
    CHAT_NOT_FOUND = "chat_not_found"
    MESSAGE_TOO_LONG = "message_too_long"
    FORBIDDEN = "forbidden"
    BAD_REQUEST = "bad_request"
    UNKNOWN_ERROR = "unknown_error"


class TelegramError(Exception):
    """Telegram API error information."""

    def __init__(
        self,
        error_type: TelegramErrorType,
        message: str,
        retry_after: Optional[int] = None,
        status_code: Optional[int] = None,
    ):
        self.error_type = error_type
        self.message = message
        self.retry_after = retry_after
        self.status_code = status_code
        super().__init__(message)


class TelegramClient:
    """Robust Telegram client with comprehensive error handling."""

    def __init__(self, parse_mode: TelegramParseMode = TelegramParseMode.HTML):
        """
        Initialize the Telegram client.

        Args:
            parse_mode: Parse mode for message formatting
        """
        self.parse_mode = parse_mode
        self.message_builder = TelegramMessageBuilder(parse_mode)
        self._last_request_time = 0
        self._token: Optional[str] = None

    def _get_token(self) -> str:
        """
        Get the Telegram bot token from secrets.

        Returns:
            Bot token

        Raises:
            TelegramError: If token cannot be retrieved
        """
        if self._token:
            return self._token

        try:
            secret_name = settings.telegram_secret_name
            secret_value = get_secret(secret_name)
            token = secret_value.get("bot_token") or secret_value.get("value")

            if not token:
                raise TelegramError(
                    error_type=TelegramErrorType.INVALID_TOKEN,
                    message="Bot token not found in secret",
                )

            self._token = token
            return token

        except Exception as e:
            logger.error(f"Failed to get Telegram token: {e}")
            raise TelegramError(
                error_type=TelegramErrorType.INVALID_TOKEN,
                message=f"Failed to retrieve bot token: {str(e)}",
            )

    def _rate_limit_delay(self) -> None:
        """Apply rate limiting delay between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < TELEGRAM_API["RATE_LIMIT_DELAY"]:
            sleep_time = TELEGRAM_API["RATE_LIMIT_DELAY"] - time_since_last
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle Telegram API response and extract error information.

        Args:
            response: HTTP response from Telegram API

        Returns:
            Response data

        Raises:
            TelegramError: If the response indicates an error
        """
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse Telegram response: {e}")
            raise TelegramError(
                error_type=TelegramErrorType.UNKNOWN_ERROR,
                message=f"Invalid response format: {str(e)}",
                status_code=response.status_code,
            )

        if not data.get("ok"):
            error_code = data.get("error_code", 0)
            description = data.get("description", "Unknown error")
            retry_after = None

            # Map error codes to error types
            if error_code == 401:
                error_type = TelegramErrorType.INVALID_TOKEN
            elif error_code == 403:
                error_type = TelegramErrorType.FORBIDDEN
            elif error_code == 400:
                error_type = TelegramErrorType.BAD_REQUEST
            elif error_code == 404:
                error_type = TelegramErrorType.CHAT_NOT_FOUND
            elif error_code == 413:
                error_type = TelegramErrorType.MESSAGE_TOO_LONG
            elif error_code == 429:
                error_type = TelegramErrorType.RATE_LIMIT
                retry_after = data.get("parameters", {}).get("retry_after")
            else:
                error_type = TelegramErrorType.UNKNOWN_ERROR

            raise TelegramError(
                error_type=error_type,
                message=description,
                retry_after=retry_after,
                status_code=error_code,
            )

        return data.get("result", {})

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        retries: int = TELEGRAM_API["MAX_RETRIES"],
    ) -> Dict[str, Any]:
        """
        Make a request to the Telegram API with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            files: File data for uploads
            retries: Number of retries

        Returns:
            Response data

        Raises:
            TelegramError: If all retries fail
        """
        token = self._get_token()
        url = f"{TELEGRAM_API['BASE_URL']}{token}{endpoint}"

        for attempt in range(retries + 1):
            try:
                self._rate_limit_delay()

                if method.upper() == "GET":
                    response = requests.get(
                        url, params=data, timeout=TELEGRAM_API["TIMEOUT"]
                    )
                else:
                    # Use data parameter when files are present, json otherwise
                    if files:
                        response = requests.post(
                            url, data=data, files=files, timeout=TELEGRAM_API["TIMEOUT"]
                        )
                    else:
                        response = requests.post(
                            url, json=data, timeout=TELEGRAM_API["TIMEOUT"]
                        )

                return self._handle_response(response)

            except TelegramError as e:
                if e.error_type == TelegramErrorType.RATE_LIMIT and e.retry_after:
                    logger.warning(f"Rate limited, waiting {e.retry_after} seconds")
                    time.sleep(e.retry_after)
                    continue
                elif e.error_type in [
                    TelegramErrorType.INVALID_TOKEN,
                    TelegramErrorType.FORBIDDEN,
                ]:
                    # Don't retry these errors
                    raise
                elif attempt < retries:
                    wait_time = TELEGRAM_API["RETRY_DELAY"] * (2**attempt)
                    logger.warning(
                        f"Request failed, retrying in {wait_time}s (attempt {attempt + 1}/{retries + 1})"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    raise

            except requests.exceptions.RequestException as e:
                if attempt < retries:
                    wait_time = TELEGRAM_API["RETRY_DELAY"] * (2**attempt)
                    logger.warning(
                        f"Network error, retrying in {wait_time}s (attempt {attempt + 1}/{retries + 1}): {e}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    raise TelegramError(
                        error_type=TelegramErrorType.NETWORK_ERROR,
                        message=f"Network error after {retries + 1} attempts: {str(e)}",
                    )

        raise TelegramError(
            error_type=TelegramErrorType.UNKNOWN_ERROR,
            message=f"Request failed after {retries + 1} attempts",
        )

    def send_message(
        self,
        chat_id: str,
        text: str,
        split_long: bool = True,
        disable_web_page_preview: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Send a message to a Telegram chat.

        Args:
            chat_id: Chat ID to send message to
            text: Message text
            split_long: Whether to split long messages
            disable_web_page_preview: Whether to disable web page previews

        Returns:
            List of sent message data

        Raises:
            TelegramError: If sending fails
        """
        try:
            # Build messages with proper formatting
            messages = self.message_builder.build_message(text, split_long)

            sent_messages = []
            for message_data in messages:
                payload = {
                    "chat_id": chat_id,
                    "disable_web_page_preview": disable_web_page_preview,
                    **message_data,
                }

                result = self._make_request(
                    "POST", TELEGRAM_API["SEND_MESSAGE_ENDPOINT"], payload
                )
                sent_messages.append(result)

                logger.info(f"Message sent to chat {chat_id}")

            return sent_messages

        except TelegramError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            raise TelegramError(
                error_type=TelegramErrorType.UNKNOWN_ERROR,
                message=f"Failed to send message: {str(e)}",
            )

    def send_file(
        self,
        chat_id: str,
        file_content: Union[str, bytes],
        filename: str,
        caption: str = "",
        mime_type: str = "text/calendar",
    ) -> Dict[str, Any]:
        """
        Send a file to a Telegram chat.

        Args:
            chat_id: Chat ID to send file to
            file_content: File content
            filename: File name
            caption: File caption
            mime_type: MIME type of the file

        Returns:
            Sent message data

        Raises:
            TelegramError: If sending fails
        """
        try:
            # Truncate caption if too long
            if len(caption) > TELEGRAM_API["MAX_CAPTION_LENGTH"]:
                logger.info(
                    f"Caption truncated from {len(caption)} to {TELEGRAM_API['MAX_CAPTION_LENGTH']} characters"
                )
                caption = caption[: TELEGRAM_API["MAX_CAPTION_LENGTH"] - 3] + "..."

            # Prepare file data
            files = {"document": (filename, file_content, mime_type)}
            data = {"chat_id": chat_id, "caption": caption}

            result = self._make_request(
                "POST", TELEGRAM_API["SEND_FILE_ENDPOINT"], data, files
            )

            logger.info(f"File sent to chat {chat_id}: {filename}")
            return result

        except TelegramError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending file: {e}")
            raise TelegramError(
                error_type=TelegramErrorType.UNKNOWN_ERROR,
                message=f"Failed to send file: {str(e)}",
            )

    def get_file_path(self, file_id: str) -> Optional[str]:
        """
        Get file path from Telegram file ID.

        Args:
            file_id: Telegram file ID

        Returns:
            File path if successful, None otherwise
        """
        try:
            data = {"file_id": file_id}
            result = self._make_request("GET", TELEGRAM_API["GET_FILE_ENDPOINT"], data)

            file_path = result.get("file_path")
            if file_path:
                logger.info(f"File path resolved for file_id {file_id}")
                return file_path
            else:
                logger.error(f"No file_path in response for file_id {file_id}")
                return None

        except TelegramError as e:
            logger.error(f"Failed to get file path for {file_id}: {e.message}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file path: {e}")
            return None

    def download_file(self, file_path: str) -> Optional[bytes]:
        """
        Download a file from Telegram.

        Args:
            file_path: File path from get_file_path

        Returns:
            File content if successful, None otherwise
        """
        try:
            token = self._get_token()
            url = f"https://api.telegram.org/file/bot{token}/{file_path}"

            self._rate_limit_delay()
            response = requests.get(url, timeout=TELEGRAM_API["TIMEOUT"])
            response.raise_for_status()

            logger.info(f"File downloaded: {file_path}")
            return response.content

        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}")
            return None

    def validate_chat_id(self, chat_id: str) -> bool:
        """
        Validate that a chat ID is accessible.

        Args:
            chat_id: Chat ID to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Try to get chat information
            data = {"chat_id": chat_id}
            self._make_request("GET", "/getChat", data)
            return True
        except TelegramError as e:
            if e.error_type == TelegramErrorType.CHAT_NOT_FOUND:
                return False
            # Other errors might be temporary, so we'll assume it's valid
            return True
        except Exception:
            return False


# Global client instance
_telegram_client: Optional[TelegramClient] = None


def get_telegram_client(
    parse_mode: TelegramParseMode = TelegramParseMode.HTML,
) -> TelegramClient:
    """
    Get the global Telegram client instance.

    Args:
        parse_mode: Parse mode for message formatting

    Returns:
        Telegram client instance
    """
    global _telegram_client
    if _telegram_client is None:
        _telegram_client = TelegramClient(parse_mode)
    return _telegram_client
