from __future__ import annotations

from typing import Any


class StrandsAgent:
    def __init__(self) -> None:
        # Placeholder for AWS Strands agent composition
        self.tools: dict[str, Any] = {}

    def register_tool(self, name: str, tool: Any) -> None:
        self.tools[name] = tool

    def handle(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
        # Minimal stub: route by intent to a registered tool
        tool = self.tools.get(intent)
        if tool is None:
            return {"error": f"unknown_intent:{intent}"}
        result = tool(payload)
        if not isinstance(result, dict):
            return {"error": "tool_invalid_return"}
        return result

    @staticmethod
    def default() -> StrandsAgent:
        from .tools.auto import auto_tool
        from .tools.chat import chat_tool
        from .tools.ingest_prescription import ingest_prescription_file_tool
        from .tools.ingest_prescription_multi import ingest_prescription_multi_tool

        agent = StrandsAgent()
        agent.register_tool("ingest_prescription_file", ingest_prescription_file_tool)
        agent.register_tool("ingest_prescription_multi", ingest_prescription_multi_tool)
        agent.register_tool("chat", chat_tool)
        agent.register_tool("auto", auto_tool)
        return agent
