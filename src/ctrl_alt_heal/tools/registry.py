from __future__ import annotations

from typing import Callable, Any

from .calendar_tool import calendar_ics_tool
from .fhir_data_tool import fhir_data_tool
from .google_auth_tool import generate_auth_url_tool, exchange_code_for_token_tool
from .google_calendar_tool import (
    create_google_calendar_event_tool,
    list_google_calendar_events_tool,
    update_google_calendar_event_tool,
    delete_google_calendar_event_tool,
)
from .search_tool import search_tool
from .prescription_extraction_tool import prescription_extraction_tool
from .user_profile_tool import update_user_profile_tool, get_user_profile_tool

tool_registry: dict[str, Callable[..., Any]] = {
    "calendar_ics_tool": calendar_ics_tool,
    "fhir_data_tool": fhir_data_tool,
    "generate_auth_url_tool": generate_auth_url_tool,
    "exchange_code_for_token_tool": exchange_code_for_token_tool,
    "create_google_calendar_event_tool": create_google_calendar_event_tool,
    "list_google_calendar_events_tool": list_google_calendar_events_tool,
    "update_google_calendar_event_tool": update_google_calendar_event_tool,
    "delete_google_calendar_event_tool": delete_google_calendar_event_tool,
    "search": search_tool,
    "prescription_extraction_tool": prescription_extraction_tool,
    "update_user_profile_tool": update_user_profile_tool,
    "get_user_profile_tool": get_user_profile_tool,
}
