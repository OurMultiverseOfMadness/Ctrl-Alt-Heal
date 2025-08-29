import logging
import re

import requests

from ctrl_alt_heal.infrastructure.secrets import get_secret
from ctrl_alt_heal.config import settings

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Telegram message limits
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
TELEGRAM_MAX_CAPTION_LENGTH = 1024


def split_message_at_natural_points(
    text: str, max_length: int = TELEGRAM_MAX_MESSAGE_LENGTH
) -> list[str]:
    """
    Splits a long message at natural break points (sentences, paragraphs, etc.)
    to fit within Telegram's message length limits.
    """
    if len(text) <= max_length:
        return [text]

    # Split by double newlines first (paragraphs)
    paragraphs = text.split("\n\n")
    if len(paragraphs) > 1:
        messages = []
        current_message = ""

        for paragraph in paragraphs:
            if len(current_message) + len(paragraph) + 2 <= max_length:
                current_message += (
                    (paragraph + "\n\n") if current_message else paragraph + "\n\n"
                )
            else:
                if current_message:
                    messages.append(current_message.strip())
                current_message = paragraph + "\n\n"

        if current_message:
            messages.append(current_message.strip())

        if len(messages) > 1:
            return messages

    # Split by single newlines
    lines = text.split("\n")
    if len(lines) > 1:
        messages = []
        current_message = ""

        for line in lines:
            if len(current_message) + len(line) + 1 <= max_length:
                current_message += (line + "\n") if current_message else line + "\n"
            else:
                if current_message:
                    messages.append(current_message.strip())
                current_message = line + "\n"

        if current_message:
            messages.append(current_message.strip())

        if len(messages) > 1:
            return messages

    # Split by sentences (periods, exclamation marks, question marks)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) > 1:
        messages = []
        current_message = ""

        for sentence in sentences:
            if len(current_message) + len(sentence) + 1 <= max_length:
                current_message += (
                    (sentence + " ") if current_message else sentence + " "
                )
            else:
                if current_message:
                    messages.append(current_message.strip())
                current_message = sentence + " "

        if current_message:
            messages.append(current_message.strip())

        if len(messages) > 1:
            return messages

    # Last resort: split by words
    words = text.split()
    messages = []
    current_message = ""

    for word in words:
        if len(current_message) + len(word) + 1 <= max_length:
            current_message += (word + " ") if current_message else word + " "
        else:
            if current_message:
                messages.append(current_message.strip())
            current_message = word + " "

    if current_message:
        messages.append(current_message.strip())

    return messages


def send_telegram_message(chat_id: str, text: str):
    """Sends a message to a Telegram chat, splitting long messages if needed."""
    logger.info("Attempting to send message to chat_id: %s", chat_id)

    # Split message if it's too long
    messages = split_message_at_natural_points(text)

    if len(messages) > 1:
        logger.info(
            f"Message is {len(text)} characters long, splitting into {len(messages)} parts"
        )

    try:
        secret_name = settings.telegram_secret_name
        logger.info("Fetching secret from Secrets Manager: %s", secret_name)

        secret_value = get_secret(secret_name)
        # Handle both JSON (with 'bot_token' key) and plain text secrets
        token = secret_value.get("bot_token") or secret_value.get("value")

        if not token:
            logger.error(
                "Error: 'bot_token' or 'value' key not found in secret, or value is empty."
            )
            return

        logger.info("Successfully retrieved bot token.")

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        headers = {"Content-Type": "application/json"}

        # Send each message part
        for i, message_part in enumerate(messages):
            if len(messages) > 1:
                logger.info(
                    f"Sending message part {i+1}/{len(messages)} ({len(message_part)} characters)"
                )

            payload = {"chat_id": chat_id, "text": message_part}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            if len(messages) > 1:
                logger.info(
                    f"Successfully sent message part {i+1}/{len(messages)} to Telegram API."
                )
            else:
                logger.info("Successfully sent message to Telegram API.")

    except KeyError:
        logger.error("Error: TELEGRAM_SECRET_NAME environment variable not set.")
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e, exc_info=True)


def get_telegram_file_path(file_id: str) -> str | None:
    """Gets the file path for a file_id from Telegram."""
    logger.info("Attempting to get file path for file_id: %s", file_id)
    try:
        secret_name = settings.telegram_secret_name
        secret_value = get_secret(secret_name)
        token = secret_value.get("bot_token") or secret_value.get("value")

        if not token:
            logger.error("Error: Telegram bot token not found in secret.")
            return None

        url = f"https://api.telegram.org/bot{token}/getFile"
        payload = {"file_id": file_id}

        response = requests.get(url, params=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        file_path = data.get("result", {}).get("file_path")
        if file_path:
            logger.info("Successfully retrieved file path: %s", file_path)
            return file_path
        else:
            logger.error("Error: 'file_path' not found in Telegram API response.")
            return None

    except Exception as e:
        logger.error(
            "An unexpected error occurred while getting file path: %s", e, exc_info=True
        )
        return None


def send_telegram_file(
    chat_id: str, file_content: str, filename: str, caption: str = ""
):
    """Sends a file to a Telegram chat, truncating long captions if needed."""
    logger.info("Attempting to send file to chat_id: %s", chat_id)
    try:
        secret_name = settings.telegram_secret_name
        secret_value = get_secret(secret_name)
        token = secret_value.get("bot_token") or secret_value.get("value")

        if not token:
            logger.error("Error: Telegram bot token not found in secret.")
            return

        url = f"https://api.telegram.org/bot{token}/sendDocument"

        # Prepare the file data
        files = {"document": (filename, file_content, "text/calendar")}

        # Truncate caption if it's too long
        if len(caption) > TELEGRAM_MAX_CAPTION_LENGTH:
            logger.info(
                f"Caption is {len(caption)} characters long, truncating to {TELEGRAM_MAX_CAPTION_LENGTH}"
            )
            caption = caption[: TELEGRAM_MAX_CAPTION_LENGTH - 3] + "..."

        data = {"chat_id": chat_id, "caption": caption}

        logger.info("Making POST request to Telegram API to send file.")
        response = requests.post(url, files=files, data=data, timeout=30)
        response.raise_for_status()
        logger.info("Successfully sent file to Telegram API.")

    except Exception as e:
        logger.error(
            "An unexpected error occurred while sending file: %s", e, exc_info=True
        )
