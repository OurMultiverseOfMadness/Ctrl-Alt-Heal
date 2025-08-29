import logging

from ctrl_alt_heal.interface.telegram_client import (
    send_telegram_message as send_message_robust,
    send_telegram_file as send_file_robust,
    get_telegram_file_path as get_file_path_robust,
    TelegramError,
    TelegramErrorType,
)

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


def send_telegram_message(chat_id: str, text: str):
    """Sends a message to a Telegram chat with robust error handling and formatting."""
    try:
        # Use the robust client for sending messages
        result = send_message_robust(chat_id, text, split_long=True)
        logger.info(f"Message sent successfully to chat {chat_id}")
        return result

    except TelegramError as e:
        logger.error(
            f"Telegram error sending message to {chat_id}: {e.error_type.value} - {e.message}"
        )

        # Try to send a fallback message for certain errors
        if e.error_type in [
            TelegramErrorType.MESSAGE_TOO_LONG,
            TelegramErrorType.BAD_REQUEST,
        ]:
            try:
                # Send as plain text without formatting
                from ctrl_alt_heal.interface.telegram_client import get_telegram_client
                from ctrl_alt_heal.utils.telegram_formatter import TelegramParseMode

                client = get_telegram_client(TelegramParseMode.PLAIN_TEXT)
                result = client.send_message(chat_id, text, split_long=True)
                logger.info(f"Fallback message sent successfully to chat {chat_id}")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback message also failed: {fallback_error}")

        # For other errors, try to send a simple error message
        try:
            error_message = (
                "I'm having trouble sending that message. Please try again in a moment."
            )
            from ctrl_alt_heal.interface.telegram_client import get_telegram_client
            from ctrl_alt_heal.utils.telegram_formatter import TelegramParseMode

            client = get_telegram_client(TelegramParseMode.PLAIN_TEXT)
            result = client.send_message(chat_id, error_message, split_long=False)
            return result
        except Exception:
            logger.error("Failed to send error message to user")

    except Exception as e:
        logger.error(
            f"Unexpected error sending message to {chat_id}: {e}", exc_info=True
        )


def get_telegram_file_path(file_id: str) -> str | None:
    """Gets the file path for a file_id from Telegram with robust error handling."""
    logger.info("Attempting to get file path for file_id: %s", file_id)
    try:
        return get_file_path_robust(file_id)
    except Exception as e:
        logger.error(f"Failed to get file path for {file_id}: {e}", exc_info=True)
        return None


def send_telegram_file(
    chat_id: str, file_content: str, filename: str, caption: str = ""
):
    """Sends a file to a Telegram chat with robust error handling."""
    try:
        # Use the robust client for sending files
        result = send_file_robust(chat_id, file_content, filename, caption)
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
        ]:
            try:
                error_message = f"I couldn't send the file '{filename}'. Please try again in a moment."
                from ctrl_alt_heal.interface.telegram_client import get_telegram_client
                from ctrl_alt_heal.utils.telegram_formatter import TelegramParseMode

                client = get_telegram_client(TelegramParseMode.PLAIN_TEXT)
                result = client.send_message(chat_id, error_message, split_long=False)
                logger.info(f"Fallback error message sent to chat {chat_id}")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback message also failed: {fallback_error}")

    except Exception as e:
        logger.error(f"Unexpected error sending file to {chat_id}: {e}", exc_info=True)
