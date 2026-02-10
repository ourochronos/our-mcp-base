"""Tests for our_mcp_base.server module."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest
from mcp.types import TextContent, Tool

from our_mcp_base.server import MCPServerBase


class TestMCPServerBaseAbstract:
    """Tests for MCPServerBase abstract class."""

    def test_is_abstract(self) -> None:
        """Should not be directly instantiable."""
        with pytest.raises(TypeError, match="abstract"):
            MCPServerBase()  # type: ignore[abstract]

    def test_concrete_implementation(self) -> None:
        """Should be implementable with minimal subclass."""

        class TestServer(MCPServerBase):
            server_name = "test-server"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return {"success": True}

        server = TestServer()
        assert server.server_name == "test-server"

    def test_default_server_name(self) -> None:
        """Should have default server name and description."""

        class TestServer(MCPServerBase):
            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return {"success": True}

        server = TestServer()
        assert server.server_name == "mcp-server"
        assert server.server_description == "MCP Server"


class TestMCPServerBaseHandleToolCall:
    """Tests for MCPServerBase._handle_tool_call method."""

    @pytest.fixture
    def test_server(self) -> MCPServerBase:
        """Create a test server implementation."""

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                if name == "success":
                    return {"success": True, "data": "test"}
                elif name == "generic_error":
                    raise RuntimeError("Unknown error")
                return {"success": False}

        return TestServer()

    @pytest.mark.asyncio
    async def test_successful_call(self, test_server: MCPServerBase) -> None:
        """Should return success response."""
        result = await test_server._handle_tool_call("success", {})
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"] == "test"

    @pytest.mark.asyncio
    async def test_generic_error(self, test_server: MCPServerBase) -> None:
        """Should handle generic exceptions."""
        result = await test_server._handle_tool_call("generic_error", {})
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Internal error" in data["error"]


class TestMCPServerBaseCustomErrorHandlers:
    """Tests for MCPServerBase with custom error handlers."""

    @pytest.mark.asyncio
    async def test_custom_error_handler(self) -> None:
        """Should use custom error handlers when provided."""

        class CustomError(Exception):
            def __init__(self, msg: str) -> None:
                self.msg = msg
                super().__init__(msg)

        def handle_custom(exc: Exception, tool_name: str) -> list[TextContent]:
            assert isinstance(exc, CustomError)
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"success": False, "error": f"Custom: {exc.msg}", "tool": tool_name}),
                )
            ]

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                if name == "custom_err":
                    raise CustomError("bad input")
                return {"success": True}

        server = TestServer(error_handlers=[(CustomError, handle_custom)])
        result = await server._handle_tool_call("custom_err", {})
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Custom: bad input" in data["error"]
        assert data["tool"] == "custom_err"

    @pytest.mark.asyncio
    async def test_custom_handler_order(self) -> None:
        """Should check custom handlers in order, first match wins."""

        class BaseError(Exception):
            pass

        class SpecificError(BaseError):
            pass

        def handle_specific(exc: Exception, tool_name: str) -> list[TextContent]:
            return [TextContent(type="text", text=json.dumps({"handler": "specific"}))]

        def handle_base(exc: Exception, tool_name: str) -> list[TextContent]:
            return [TextContent(type="text", text=json.dumps({"handler": "base"}))]

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                raise SpecificError("oops")

        # SpecificError listed first -- should match
        server = TestServer(error_handlers=[(SpecificError, handle_specific), (BaseError, handle_base)])
        result = await server._handle_tool_call("tool", {})
        data = json.loads(result[0].text)
        assert data["handler"] == "specific"

    @pytest.mark.asyncio
    async def test_unmatched_falls_through_to_default(self) -> None:
        """Should fall through to default handler if no custom handler matches."""

        class UnhandledError(Exception):
            pass

        class HandledError(Exception):
            pass

        def handle_handled(exc: Exception, tool_name: str) -> list[TextContent]:
            return [TextContent(type="text", text=json.dumps({"handler": "handled"}))]

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                raise UnhandledError("nope")

        server = TestServer(error_handlers=[(HandledError, handle_handled)])
        result = await server._handle_tool_call("tool", {})
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Internal error" in data["error"]


class TestMCPServerBaseParseArgs:
    """Tests for MCPServerBase.parse_args method."""

    def test_parse_args_no_hooks(self) -> None:
        """Should parse empty args when no hooks configured."""

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return {}

        server = TestServer()
        with patch("sys.argv", ["test"]):
            args = server.parse_args()
            # No health_check or skip_startup_hook attributes
            assert not hasattr(args, "health_check")
            assert not hasattr(args, "skip_startup_hook")

    def test_parse_args_with_health_check(self) -> None:
        """Should parse --health-check when health_check is provided."""

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return {}

        server = TestServer(health_check=lambda: 0)
        with patch("sys.argv", ["test", "--health-check"]):
            args = server.parse_args()
            assert args.health_check is True

    def test_parse_args_with_startup_hook(self) -> None:
        """Should parse --skip-startup-hook when startup_hook is provided."""

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return {}

        server = TestServer(startup_hook=lambda: None)
        with patch("sys.argv", ["test", "--skip-startup-hook"]):
            args = server.parse_args()
            assert args.skip_startup_hook is True


class TestMCPServerBaseRun:
    """Tests for MCPServerBase.run method."""

    def test_health_check_mode(self) -> None:
        """Should run health check and exit in health check mode."""

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return {}

        server = TestServer(health_check=lambda: 0)

        with patch("sys.argv", ["test", "--health-check"]):
            with pytest.raises(SystemExit) as exc_info:
                server.run()
            assert exc_info.value.code == 0

    def test_health_check_unhealthy(self) -> None:
        """Should exit with non-zero code when health check fails."""

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return {}

        server = TestServer(health_check=lambda: 1)

        with patch("sys.argv", ["test", "--health-check"]):
            with pytest.raises(SystemExit) as exc_info:
                server.run()
            assert exc_info.value.code == 1

    def test_startup_hook_called(self) -> None:
        """Should call startup hook during normal run."""
        hook_called = False

        def my_hook() -> None:
            nonlocal hook_called
            hook_called = True

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return {}

        server = TestServer(startup_hook=my_hook)

        with patch("sys.argv", ["test"]):
            with patch("asyncio.run"):
                server.run()

        assert hook_called is True

    def test_startup_hook_skipped(self) -> None:
        """Should skip startup hook when --skip-startup-hook is set."""
        hook_called = False

        def my_hook() -> None:
            nonlocal hook_called
            hook_called = True

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return {}

        server = TestServer(startup_hook=my_hook)

        with patch("sys.argv", ["test", "--skip-startup-hook"]):
            with patch("asyncio.run"):
                server.run()

        assert hook_called is False

    def test_no_hooks_runs_server(self) -> None:
        """Should run server even with no hooks configured."""

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return {}

        server = TestServer()

        with patch("sys.argv", ["test"]):
            with patch("asyncio.run") as mock_run:
                server.run()
            mock_run.assert_called_once()

    def test_startup_hook_failure_propagates(self) -> None:
        """Should propagate startup hook failures."""

        def failing_hook() -> None:
            raise RuntimeError("DB connection failed")

        class TestServer(MCPServerBase):
            server_name = "test"

            def get_tools(self) -> list[Tool]:
                return []

            def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return {}

        server = TestServer(startup_hook=failing_hook)

        with patch("sys.argv", ["test"]):
            with pytest.raises(RuntimeError, match="DB connection failed"):
                server.run()
