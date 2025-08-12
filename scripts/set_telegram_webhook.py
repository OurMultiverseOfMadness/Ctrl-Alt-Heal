from __future__ import annotations

import os
import sys

import requests


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    api_url = os.environ.get("TELEGRAM_API_URL", "https://api.telegram.org")
    webhook_url = os.environ.get("WEBHOOK_URL")
    secret_token = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
    if not token or not webhook_url or not secret_token:
        print(
            "Missing TELEGRAM_BOT_TOKEN/WEBHOOK_URL/TELEGRAM_WEBHOOK_SECRET",
            file=sys.stderr,
        )
        return 2
    url = f"{api_url}/bot{token}/setWebhook"
    resp = requests.post(
        url,
        json={
            "url": webhook_url,
            "allowed_updates": [
                "message",
                "edited_message",
                "callback_query",
                "channel_post",
                "chat_member",
            ],
            "secret_token": secret_token,
            "drop_pending_updates": True,
        },
        timeout=15,
    )
    print(resp.status_code, resp.text)
    return 0 if resp.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
