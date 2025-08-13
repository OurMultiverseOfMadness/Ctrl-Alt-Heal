from __future__ import annotations

import logging
import os

_configured = False


def _configure_once() -> None:
    global _configured
    if _configured:
        return
    level_name = os.getenv("LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.INFO)
    # In AWS Lambda, a default handler is pre-configured at WARNING.
    # Force reconfigure so INFO/DEBUG logs appear.
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )
    # Silence noisy third-party loggers by default
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    _configure_once()
    return logging.getLogger(name or __name__)
