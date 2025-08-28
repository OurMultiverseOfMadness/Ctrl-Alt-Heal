import logging

import requests

from ctrl_alt_heal.infrastructure.secrets import get_secret
from ctrl_alt_heal.config import settings

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def send_telegram_message(chat_id: str, text: str):
    """Sends a message to a Telegram chat."""
    logger.info("Attempting to send message to chat_id: %s", chat_id)
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
        payload = {"chat_id": chat_id, "text": text}
        headers = {"Content-Type": "application/json"}

        logger.info("Making POST request to Telegram API.")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
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
    """Sends a file to a Telegram chat."""
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

        data = {"chat_id": chat_id, "caption": caption}

        logger.info("Making POST request to Telegram API to send file.")
        response = requests.post(url, files=files, data=data, timeout=30)
        response.raise_for_status()
        logger.info("Successfully sent file to Telegram API.")

    except Exception as e:
        logger.error(
            "An unexpected error occurred while sending file: %s", e, exc_info=True
        )
