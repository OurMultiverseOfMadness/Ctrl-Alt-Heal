import logging
import os

import requests

from ctrl_alt_heal.infrastructure.secrets import get_secret

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def send_telegram_message(chat_id: str, text: str):
    """Sends a message to a Telegram chat."""
    logger.info("Attempting to send message to chat_id: %s", chat_id)
    try:
        secret_name = os.environ["TELEGRAM_SECRET_NAME"]
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
