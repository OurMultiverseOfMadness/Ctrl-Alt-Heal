from __future__ import annotations

import logging
import os

_configured = False


def _configure_once() -> None:
    global _configured
    if _configured:
        return
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    _configure_once()
    return logging.getLogger(name or __name__)
