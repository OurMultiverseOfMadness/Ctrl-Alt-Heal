from __future__ import annotations

from typing import Any, Callable

from .prescription_extraction_tool import prescription_extraction_tool
from .image_description_tool import describe_image_tool

# A simple registry for tools that need to be manually invoked
tool_registry: dict[str, Callable[..., Any]] = {
    "prescription_extraction": prescription_extraction_tool,
    "describe_image": describe_image_tool,
}
