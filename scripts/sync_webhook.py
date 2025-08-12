from __future__ import annotations

import os
import sys
from typing import Any

import boto3
import requests


def get_stack_output(
    name: str, *, profile: str | None = None, region: str | None = None
) -> dict[str, str]:
    session = boto3.session.Session(profile_name=profile, region_name=region)
    cfn = session.client("cloudformation")
    resp = cfn.describe_stacks(StackName=name)
    stacks = resp.get("Stacks", [])
    if not stacks:
        raise RuntimeError(f"Stack not found: {name}")
    outputs = stacks[0].get("Outputs", [])
    out: dict[str, str] = {}
    for o in outputs:
        key = o.get("OutputKey")
        val = o.get("OutputValue")
        if isinstance(key, str) and isinstance(val, str):
            out[key] = val
    return out


def get_secret(
    secret_id: str, *, profile: str | None = None, region: str | None = None
) -> str | None:
    session = boto3.session.Session(profile_name=profile, region_name=region)
    sm = session.client("secretsmanager")
    try:
        resp = sm.get_secret_value(SecretId=secret_id)
        val = resp.get("SecretString")
        return str(val) if isinstance(val, str) else None
    except Exception:
        return None


def get_webhook_info(token: str, api_url: str) -> dict[str, Any]:
    url = f"{api_url}/bot{token}/getWebhookInfo"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data_obj = r.json()
    result: dict[str, Any] = {}
    if isinstance(data_obj, dict):
        result = data_obj
    else:
        raise ValueError("Invalid webhook info JSON structure")
    return result


def set_webhook(token: str, api_url: str, webhook_url: str, secret: str | None) -> None:
    url = f"{api_url}/bot{token}/setWebhook"
    payload: dict[str, Any] = {
        "url": webhook_url,
        "allowed_updates": [
            "message",
            "edited_message",
            "callback_query",
            "channel_post",
            "chat_member",
        ],
        "drop_pending_updates": False,
    }
    if secret:
        payload["secret_token"] = secret
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()


def main() -> int:
    profile = os.environ.get("AWS_PROFILE")
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    api_url = os.environ.get("TELEGRAM_API_URL", "https://api.telegram.org")
    stack_name = os.environ.get("CDK_STACK_NAME", "CtrlAltHealStack")

    # Token: env var preferred locally; otherwise from Secrets Manager
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or get_secret(
        "ctrl-alt-heal/telegram/bot-token", profile=profile, region=region
    )
    if not token:
        print(
            "Missing TELEGRAM_BOT_TOKEN and secret ctrl-alt-heal/telegram/bot-token",
            file=sys.stderr,
        )
        return 2

    # Expected webhook URL: from env or CFN output
    expected = os.environ.get("WEBHOOK_URL")
    if not expected:
        outs = get_stack_output(stack_name, profile=profile, region=region)
        base = outs.get("HttpApiUrl")
        if not base:
            print("Missing HttpApiUrl output in stack", file=sys.stderr)
            return 3
        expected = f"{base}/telegram/webhook"

    # Current Telegram webhook
    info = get_webhook_info(token, api_url)
    current = info.get("result", {}).get("url") if info.get("ok") else None

    if current == expected:
        print("Webhook already up-to-date:", expected)
        return 0

    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET") or get_secret(
        "ctrl-alt-heal/telegram/webhook-secret", profile=profile, region=region
    )
    set_webhook(token, api_url, expected, secret)
    print("Webhook set to:", expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
