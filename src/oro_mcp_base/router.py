"""Tool routing helper for MCP servers.

Provides a decorator-based registry for dispatching tool calls to handler functions.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .responses import error_response


class ToolRouter:
    """Simple tool routing helper.

    Allows registering tool handlers and dispatching to them by name.

    Example:
        router = ToolRouter()

        @router.register("my_tool")
        def handle_my_tool(arg1: str, arg2: int = 10) -> dict:
            return {"success": True, "result": arg1 * arg2}

        # In handle_tool:
        result = router.dispatch(name, arguments)
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., dict[str, Any]]] = {}

    def register(self, name: str) -> Callable[[Callable[..., dict[str, Any]]], Callable[..., dict[str, Any]]]:
        """Decorator to register a tool handler.

        Args:
            name: Tool name to register
        """

        def decorator(func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
            self._handlers[name] = func
            return func

        return decorator

    def dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Dispatch to the appropriate handler.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Handler result or error if tool not found
        """
        handler = self._handlers.get(name)
        if handler is None:
            return error_response(f"Unknown tool: {name}")
        return handler(**arguments)

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._handlers

    @property
    def tool_names(self) -> list[str]:
        """Get list of registered tool names."""
        return list(self._handlers.keys())
