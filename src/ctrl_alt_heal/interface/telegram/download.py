from __future__ import annotations

import json as _json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

import boto3

from ...config.settings import Settings


@dataclass(frozen=True)
class DownloadResult:
    s3_bucket: str
    s3_key: str
    file_mime_type: str | None


def _get_bot_token(settings: Settings) -> str:
    token = settings.telegram_bot_token
    token_arn = settings.telegram_bot_token_secret_arn
    if token_arn:
        sm = boto3.client("secretsmanager")
        try:
            resp = sm.get_secret_value(SecretId=token_arn)
            secret_val = resp.get("SecretString")
            if isinstance(secret_val, str):
                token = secret_val
        except Exception:
            pass
    if not token:
        raise RuntimeError("Telegram bot token not configured")
    return token


def _telegram_api_base(settings: Settings) -> str:
    return settings.telegram_api_url


def _resolve_file_path(settings: Settings, token: str, file_id: str) -> str:
    url = f"{_telegram_api_base(settings)}/bot{token}/getFile?file_id={file_id}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:  # nosec B310
            body = r.read()
    except urllib.error.URLError as exc:
        raise RuntimeError("Telegram getFile failed") from exc
    data: dict[str, Any] = _json.loads(body.decode("utf-8"))
    if not data.get("ok"):
        raise RuntimeError("Telegram getFile failed")
    result = data.get("result", {})
    file_path = result.get("file_path")
    if not isinstance(file_path, str):
        raise RuntimeError("Missing file_path")
    return file_path


def _download_file(settings: Settings, token: str, file_path: str) -> bytes:
    url = f"{_telegram_api_base(settings)}/file/bot{token}/{file_path}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:  # nosec B310
            return r.read()
    except urllib.error.URLError as exc:
        raise RuntimeError("Telegram file download failed") from exc


def download_and_store_telegram_file(
    update: dict[str, Any], settings: Settings | None = None
) -> DownloadResult:
    settings = settings or Settings.load()
    message = update.get("message") or update.get("edited_message") or {}
    # Prefer documents; else take the best photo size
    file_id: str | None = None
    mime_type: str | None = None
    if "document" in message:
        doc = message["document"]
        file_id = doc.get("file_id")
        mime_type = doc.get("mime_type")
    elif "photo" in message:
        photos = message["photo"]
        if isinstance(photos, list) and photos:
            file_id = photos[-1].get("file_id")
    if not file_id:
        raise ValueError("No file found in update")

    token = _get_bot_token(settings)
    file_path = _resolve_file_path(settings, token, file_id)
    blob = _download_file(settings, token, file_path)

    bucket = settings.docs_bucket
    if not bucket:
        raise RuntimeError("DOCS_BUCKET not set")

    # Create a deterministic S3 key using Telegram file path
    s3_key = f"telegram/{file_path}"
    s3 = boto3.client("s3")
    extra: dict[str, Any] = {}
    if mime_type:
        extra["ContentType"] = mime_type
    s3.put_object(Bucket=bucket, Key=s3_key, Body=blob, **extra)
    return DownloadResult(s3_bucket=bucket, s3_key=s3_key, file_mime_type=mime_type)
