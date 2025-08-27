import requests

from ctrl_alt_heal.config import settings


class TelegramClient:
    def __init__(self) -> None:
        self.bot_token = settings.telegram_bot_token
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_message(self, chat_id: str, text: str) -> None:
        """Sends a message to a Telegram chat."""
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending message to Telegram: {e}")
