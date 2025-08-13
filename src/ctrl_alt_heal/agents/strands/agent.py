from __future__ import annotations

from collections.abc import Callable, Callable as TypingCallable
from typing import Any, cast

from strands import Agent as SdkAgent, tool as sdk_tool


class StrandsAgent:
    def __init__(self) -> None:
        # Registry for plain-callable tools by intent name
        self.tools: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
        # Optional: real Strands SDK agent to host decorated tools
        self._sdk_agent: SdkAgent | None = None
        self._sdk_tools: dict[str, Callable[..., dict[str, Any]]] = {}

    def register_tool(
        self, name: str, tool: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> None:
        self.tools[name] = tool

    def handle(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
        # Route by intent to a registered tool (plain Python call)
        fn = self.tools.get(intent)
        if fn is None:
            return {"error": f"unknown_intent:{intent}"}
        result = fn(payload)
        if not isinstance(result, dict):
            return {"error": "tool_invalid_return"}
        return result

    def handle_sdk(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
        # Route to our decorated wrappers directly to avoid name mismatches
        fn = self._sdk_tools.get(intent)
        if fn is None:
            return {"error": f"unknown_intent:{intent}"}
        try:
            if intent in {
                "auto",
                "ingest_prescription_file",
                "ingest_prescription_multi",
            }:
                update = payload.get("update")
                if not isinstance(update, dict):
                    return {"error": "missing_update"}
                return fn(update)
            if intent == "chat":
                text = payload.get("text")
                if not isinstance(text, str) or not text.strip():
                    return {"error": "empty_text"}
                return fn(text)
            return {"error": f"unsupported_intent:{intent}"}
        except Exception as exc:  # pragma: no cover
            return {"error": f"sdk_error:{exc}"}

    @staticmethod
    def default() -> StrandsAgent:
        from .tools.auto import auto_tool
        from .tools.chat import chat_tool
        from .tools.ingest_prescription import ingest_prescription_file_tool
        from .tools.ingest_prescription_multi import ingest_prescription_multi_tool

        # Create plain agent and register direct-call tools
        agent = StrandsAgent()
        agent.register_tool("ingest_prescription_file", ingest_prescription_file_tool)
        agent.register_tool("ingest_prescription_multi", ingest_prescription_multi_tool)
        agent.register_tool("chat", chat_tool)
        agent.register_tool("auto", auto_tool)

        # Build SDK-decorated wrappers to host in the real Strands SDK agent
        sdk_tool_typed: TypingCallable[..., TypingCallable[..., dict[str, Any]]] = cast(
            Any, sdk_tool
        )

        @sdk_tool_typed(
            description="Ingest a single prescription file from a Telegram update",
            inputSchema={
                "type": "object",
                "properties": {"update": {"type": "object"}},
                "required": ["update"],
            },
        )
        def sdk_ingest_prescription_file(update: dict[str, Any]) -> dict[str, Any]:
            return ingest_prescription_file_tool({"update": update})

        @sdk_tool_typed(
            description="Ingest a multi-medication prescription from a Telegram update",
            inputSchema={
                "type": "object",
                "properties": {"update": {"type": "object"}},
                "required": ["update"],
            },
        )
        def sdk_ingest_prescription_multi(update: dict[str, Any]) -> dict[str, Any]:
            return ingest_prescription_multi_tool({"update": update})

        @sdk_tool_typed(
            description="General chat over Bedrock",
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        )
        def sdk_chat(text: str) -> dict[str, Any]:
            return chat_tool({"text": text})

        @sdk_tool_typed(
            description="Auto-router for Telegram updates",
            inputSchema={
                "type": "object",
                "properties": {"update": {"type": "object"}},
                "required": ["update"],
            },
        )
        def sdk_auto(update: dict[str, Any]) -> dict[str, Any]:
            return auto_tool({"update": update})

        # Host the SDK tools
        agent._sdk_agent = SdkAgent(
            tools=[
                sdk_ingest_prescription_file,
                sdk_ingest_prescription_multi,
                sdk_chat,
                sdk_auto,
            ]
        )

        # Map canonical names to decorated callables
        agent._sdk_tools = {
            "ingest_prescription_file": cast(
                Callable[..., dict[str, Any]], sdk_ingest_prescription_file
            ),
            "ingest_prescription_multi": cast(
                Callable[..., dict[str, Any]], sdk_ingest_prescription_multi
            ),
            "chat": cast(Callable[..., dict[str, Any]], sdk_chat),
            "auto": cast(Callable[..., dict[str, Any]], sdk_auto),
        }

        return agent
