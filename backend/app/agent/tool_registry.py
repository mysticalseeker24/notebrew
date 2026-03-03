"""Tool registry — maps tool names to implementations and OpenAI function schemas."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Awaitable

from app.models import ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for agent tools.

    Stores tool metadata (name, description, JSON schema) alongside the
    handler function. Provides tool definitions in the OpenAI
    function-calling format and executes tools by name.
    """

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[..., Awaitable[Any]],
    ) -> None:
        """Register a tool with its schema and handler.

        Args:
            name: Unique tool name (e.g., 'parse_pdf').
            description: Human-readable description for the LLM.
            parameters: JSON Schema dict describing the tool's parameters.
            handler: Async function that executes the tool.
        """
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
        }
        logger.info("Registered tool: %s", name)

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return tool definitions in OpenAI function-calling format.

        Returns:
            List of dicts, each with 'type' = 'function' and a 'function'
            object containing name, description, and parameters.
        """
        definitions = []
        for tool in self._tools.values():
            definitions.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    },
                }
            )
        return definitions

    async def execute(
        self, tool_name: str, arguments: dict[str, Any], tool_call_id: str
    ) -> ToolResult:
        """Execute a registered tool by name.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Keyword arguments to pass to the tool handler.
            tool_call_id: ID of the tool call (for result mapping).

        Returns:
            ToolResult with success/failure and the result or error message.
        """
        if tool_name not in self._tools:
            return ToolResult(
                tool_call_id=tool_call_id,
                name=tool_name,
                success=False,
                error=f"Unknown tool: {tool_name}",
            )

        handler = self._tools[tool_name]["handler"]
        try:
            result = await handler(**arguments)
            return ToolResult(
                tool_call_id=tool_call_id,
                name=tool_name,
                success=True,
                result=result,
            )
        except Exception as exc:
            logger.exception("Tool %s failed", tool_name)
            return ToolResult(
                tool_call_id=tool_call_id,
                name=tool_name,
                success=False,
                error=str(exc),
            )

    async def execute_parallel(
        self, calls: list[dict[str, Any]]
    ) -> list[ToolResult]:
        """Execute multiple tool calls concurrently.

        Args:
            calls: List of dicts with 'name', 'arguments', and 'tool_call_id'.

        Returns:
            List of ToolResult objects in the same order as the input calls.
        """
        tasks = [
            self.execute(
                tool_name=call["name"],
                arguments=call["arguments"],
                tool_call_id=call["tool_call_id"],
            )
            for call in calls
        ]
        return await asyncio.gather(*tasks)

    @property
    def tool_names(self) -> list[str]:
        """Return list of registered tool names."""
        return list(self._tools.keys())
