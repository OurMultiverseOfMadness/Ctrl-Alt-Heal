from __future__ import annotations

from src.ctrl_alt_heal.interface.telegram.handlers.router import route_update


def test_route_message() -> None:
    assert route_update({"message": {"text": "hi"}})["type"] == "message"


def test_route_unknown() -> None:
    assert route_update({})["type"] == "unknown"
