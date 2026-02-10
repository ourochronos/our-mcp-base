"""Tests for our_mcp_base.router module."""

from __future__ import annotations

from typing import Any

from our_mcp_base.router import ToolRouter


class TestToolRouter:
    """Tests for ToolRouter class."""

    def test_register_decorator(self) -> None:
        """Should register handlers via decorator."""
        router = ToolRouter()

        @router.register("test_tool")
        def handler(arg1: str) -> dict[str, Any]:
            return {"result": arg1}

        assert router.has_tool("test_tool")

    def test_dispatch_to_handler(self) -> None:
        """Should dispatch to registered handler."""
        router = ToolRouter()

        @router.register("my_tool")
        def handler(value: int) -> dict[str, Any]:
            return {"success": True, "doubled": value * 2}

        result = router.dispatch("my_tool", {"value": 5})
        assert result["success"] is True
        assert result["doubled"] == 10

    def test_dispatch_unknown_tool(self) -> None:
        """Should return error for unknown tool."""
        router = ToolRouter()
        result = router.dispatch("nonexistent", {})
        assert result["success"] is False
        assert "Unknown tool" in result["error"]

    def test_has_tool(self) -> None:
        """Should check if tool is registered."""
        router = ToolRouter()

        @router.register("exists")
        def handler() -> dict[str, Any]:
            return {}

        assert router.has_tool("exists") is True
        assert router.has_tool("not_exists") is False

    def test_tool_names(self) -> None:
        """Should return list of registered tool names."""
        router = ToolRouter()

        @router.register("tool_a")
        def a() -> dict[str, Any]:
            return {}

        @router.register("tool_b")
        def b() -> dict[str, Any]:
            return {}

        names = router.tool_names
        assert "tool_a" in names
        assert "tool_b" in names
        assert len(names) == 2

    def test_multiple_handlers(self) -> None:
        """Should handle multiple registered tools."""
        router = ToolRouter()

        @router.register("add")
        def add_handler(a: int, b: int) -> dict[str, Any]:
            return {"result": a + b}

        @router.register("multiply")
        def mul_handler(a: int, b: int) -> dict[str, Any]:
            return {"result": a * b}

        assert router.dispatch("add", {"a": 3, "b": 4})["result"] == 7
        assert router.dispatch("multiply", {"a": 3, "b": 4})["result"] == 12

    def test_register_preserves_function(self) -> None:
        """Should return the original function from the decorator."""
        router = ToolRouter()

        @router.register("my_tool")
        def handler(x: int) -> dict[str, Any]:
            return {"x": x}

        # The decorator should return the original function
        result = handler(x=42)
        assert result == {"x": 42}
