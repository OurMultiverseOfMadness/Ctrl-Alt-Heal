import logging
from typing import List, Dict, Any, Union, Optional

from ctrl_alt_heal.interface.telegram_client import (
    TelegramError,
    TelegramErrorType,
    get_telegram_client,
)
from ctrl_alt_heal.utils.telegram_formatter import TelegramParseMode

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Legacy function for backward compatibility
def split_message_at_natural_points(text: str, max_length: int = 4096) -> list[str]:
    """
    Legacy function for backward compatibility.
    Now uses the robust message builder internally.
    """
    from ctrl_alt_heal.utils.telegram_formatter import MessageSplitter

    splitter = MessageSplitter(max_length)
    return splitter.split_message(text, preserve_formatting=True)


def send_telegram_message(
    chat_id: str,
    text: str,
    parse_mode: TelegramParseMode = TelegramParseMode.HTML,
    split_long: bool = True,
) -> List[Dict[str, Any]]:
    """
    Sends a message to a Telegram chat with robust error handling and formatting.

    Args:
        chat_id: Chat ID to send message to
        text: Message text to send
        parse_mode: Parse mode for formatting (HTML, Markdown, or Plain Text)
        split_long: Whether to split long messages automatically

    Returns:
        List of sent message data

    Raises:
        TelegramError: If sending fails after all retry attempts
    """
    try:
        # Use the robust client with specified parse mode
        client = get_telegram_client(parse_mode)
        result = client.send_message(chat_id, text, split_long=split_long)
        logger.info(
            f"Message sent successfully to chat {chat_id} using {parse_mode.value} mode"
        )
        return result

    except TelegramError as e:
        logger.error(
            f"Telegram error sending message to {chat_id}: {e.error_type.value} - {e.message}"
        )

        # Try to send a fallback message for certain errors
        if e.error_type in [
            TelegramErrorType.MESSAGE_TOO_LONG,
            TelegramErrorType.BAD_REQUEST,
            TelegramErrorType.FORBIDDEN,
        ]:
            try:
                # Send as plain text without formatting
                fallback_client = get_telegram_client(TelegramParseMode.PLAIN_TEXT)
                result = fallback_client.send_message(chat_id, text, split_long=True)
                logger.info(
                    f"Fallback message sent successfully to chat {chat_id} using plain text"
                )
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback message also failed: {fallback_error}")

        # For other errors, try to send a simple error message
        try:
            error_message = (
                "I'm having trouble sending that message. Please try again in a moment."
            )
            error_client = get_telegram_client(TelegramParseMode.PLAIN_TEXT)
            result = error_client.send_message(chat_id, error_message, split_long=False)
            logger.info(f"Error message sent to chat {chat_id}")
            return result
        except Exception:
            logger.error("Failed to send error message to user")
            # Re-raise the original error if we can't even send an error message
            raise e

    except Exception as e:
        logger.error(
            f"Unexpected error sending message to {chat_id}: {e}", exc_info=True
        )
        raise


def get_telegram_file_path(file_id: str) -> Optional[str]:
    """
    Gets the file path for a file_id from Telegram with robust error handling.

    Args:
        file_id: Telegram file ID

    Returns:
        File path if successful, None otherwise
    """
    logger.info("Attempting to get file path for file_id: %s", file_id)
    try:
        client = get_telegram_client()
        result = client.get_file_path(file_id)
        if result:
            logger.info(f"Successfully retrieved file path for {file_id}")
        else:
            logger.warning(f"File path not found for {file_id}")
        return result
    except TelegramError as e:
        logger.error(
            f"Telegram error getting file path for {file_id}: {e.error_type.value} - {e.message}"
        )
        return None
    except Exception as e:
        logger.error(f"Failed to get file path for {file_id}: {e}", exc_info=True)
        return None


def send_telegram_file(
    chat_id: str,
    file_content: Union[str, bytes],
    filename: str,
    caption: str = "",
    parse_mode: TelegramParseMode = TelegramParseMode.HTML,
) -> Optional[Dict[str, Any]]:
    """
    Sends a file to a Telegram chat with robust error handling.

    Args:
        chat_id: Chat ID to send file to
        file_content: File content (string or bytes)
        filename: File name
        caption: File caption (optional)
        parse_mode: Parse mode for caption formatting

    Returns:
        Sent message data if successful, None otherwise
    """
    try:
        # Use the robust client for sending files
        client = get_telegram_client(parse_mode)
        result = client.send_file(chat_id, file_content, filename, caption)
        logger.info(f"File sent successfully to chat {chat_id}: {filename}")
        return result

    except TelegramError as e:
        logger.error(
            f"Telegram error sending file to {chat_id}: {e.error_type.value} - {e.message}"
        )

        # Try to send a fallback message for certain errors
        if e.error_type in [
            TelegramErrorType.MESSAGE_TOO_LONG,
            TelegramErrorType.BAD_REQUEST,
            TelegramErrorType.FORBIDDEN,
        ]:
            try:
                error_message = f"I couldn't send the file '{filename}'. Please try again in a moment."
                error_client = get_telegram_client(TelegramParseMode.PLAIN_TEXT)
                result = error_client.send_message(
                    chat_id, error_message, split_long=False
                )
                logger.info(f"Fallback error message sent to chat {chat_id}")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback message also failed: {fallback_error}")

        # For other errors, try to send a simple error message
        try:
            error_message = (
                "I'm having trouble sending files right now. Please try again later."
            )
            error_client = get_telegram_client(TelegramParseMode.PLAIN_TEXT)
            result = error_client.send_message(chat_id, error_message, split_long=False)
            logger.info(f"Error message sent to chat {chat_id}")
            return result
        except Exception:
            logger.error("Failed to send error message to user")

    except Exception as e:
        logger.error(f"Unexpected error sending file to {chat_id}: {e}", exc_info=True)

    return None


def validate_telegram_chat_id(chat_id: str) -> bool:
    """
    Validates that a chat ID is accessible with the current bot token.

    Args:
        chat_id: Chat ID to validate

    Returns:
        True if valid and accessible, False otherwise
    """
    try:
        client = get_telegram_client()
        return client.validate_chat_id(chat_id)
    except Exception as e:
        logger.error(f"Error validating chat ID {chat_id}: {e}")
        return False


def send_telegram_message_with_retry(
    chat_id: str,
    text: str,
    max_retries: int = 3,
    parse_mode: TelegramParseMode = TelegramParseMode.HTML,
) -> Optional[List[Dict[str, Any]]]:
    """
    Sends a message to Telegram with automatic retry logic.

    Args:
        chat_id: Chat ID to send message to
        text: Message text
        max_retries: Maximum number of retry attempts
        parse_mode: Parse mode for formatting

    Returns:
        List of sent message data if successful, None otherwise
    """
    for attempt in range(max_retries):
        try:
            return send_telegram_message(chat_id, text, parse_mode)
        except TelegramError as e:
            if e.error_type in [
                TelegramErrorType.RATE_LIMIT,
                TelegramErrorType.NETWORK_ERROR,
            ]:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_retries} for chat {chat_id}"
                    )
                    continue
            # For other errors or max retries reached, don't retry
            logger.error(f"Failed to send message after {max_retries} attempts: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                continue
            return None

    return None
