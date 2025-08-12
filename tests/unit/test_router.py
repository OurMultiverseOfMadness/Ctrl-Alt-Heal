from __future__ import annotations

from src.ctrl_alt_heal.interface.telegram.handlers.router import (
    parse_command,
    route_update,
)


def test_route_message() -> None:
    assert route_update({"message": {"text": "hi"}})["type"] == "message"


def test_route_unknown() -> None:
    assert route_update({})["type"] == "unknown"


def test_parse_command() -> None:
    cmd, args = parse_command({"message": {"text": "/start"}})
    assert cmd == "start" and args is None
    cmd, args = parse_command({"message": {"text": "/schedule 9am"}})
    assert cmd == "schedule" and args == "9am"
