from __future__ import annotations

from typing import Any, Callable

from .prescription_extraction_tool import prescription_extraction_tool
from .image_description_tool import describe_image_tool
from .fhir_data_tool import fhir_data_tool
from .calendar_tool import calendar_ics_tool
from .search_tool import search_tool
from .user_profile_tool import (
    update_user_profile_tool,
    get_user_profile_tool,
    save_user_notes_tool,
)
from .identity_tool import (
    find_user_by_identity_tool,
    create_user_with_identity_tool,
    get_or_create_user_tool,
)

# A simple registry for tools that need to be manually invoked
tool_registry: dict[str, Callable[..., Any]] = {
    "prescription_extraction": prescription_extraction_tool,
    "describe_image": describe_image_tool,
    "fhir_data": fhir_data_tool,
    "calendar_ics": calendar_ics_tool,
    "search": search_tool,
    "update_user_profile": update_user_profile_tool,
    "get_user_profile": get_user_profile_tool,
    "save_user_notes": save_user_notes_tool,
    "find_user_by_identity": find_user_by_identity_tool,
    "create_user_with_identity": create_user_with_identity_tool,
    "get_or_create_user": get_or_create_user_tool,
}
