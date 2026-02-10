"""Base class for MCP servers.

Provides common patterns for tool routing, error handling, and response formatting
to reduce duplication across MCP servers. External dependencies (startup hooks,
health checks) are injectable rather than hardcoded.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)


class MCPServerBase(ABC):
    """Base class for MCP servers.

    Provides common functionality:
    - Argument parsing with optional health check support
    - Optional startup hook (e.g., schema initialization)
    - Optional health check callable
    - Error handling in tool calls
    - JSON response formatting

    Subclasses should implement:
    - server_name: The MCP server name
    - get_tools(): Return list of Tool definitions
    - handle_tool(): Handle tool calls

    External dependencies are injectable:
    - startup_hook: Called during server startup (e.g., DB schema init)
    - health_check: Called for --health-check flag, returns exit code (0=healthy)
    - error_handlers: Additional exception handlers for tool calls

    Example:
        class MyServer(MCPServerBase):
            server_name = "my-server"

            def get_tools(self) -> list[Tool]:
                return [Tool(name="my_tool", ...)]

            def handle_tool(self, name: str, arguments: dict) -> dict:
                if name == "my_tool":
                    return {"success": True, "data": "..."}
                return {"success": False, "error": f"Unknown tool: {name}"}

        if __name__ == "__main__":
            MyServer().run()

        # With optional hooks:
        MyServer(
            startup_hook=lambda: init_db(),
            health_check=lambda: check_db_health(),
        ).run()
    """

    server_name: str = "mcp-server"
    server_description: str = "MCP Server"

    def __init__(
        self,
        startup_hook: Callable[[], None] | None = None,
        health_check: Callable[[], int] | None = None,
        error_handlers: list[tuple[type[Exception], Callable[[Exception, str], list[TextContent]]]] | None = None,
    ) -> None:
        """Initialize the MCP server.

        Args:
            startup_hook: Optional callable invoked during server startup (e.g., DB init).
                          Should raise on fatal errors.
            health_check: Optional callable for --health-check mode. Returns exit code
                          (0 = healthy, non-zero = unhealthy).
            error_handlers: Optional list of (ExceptionType, handler) tuples for custom
                            error handling in tool calls. Checked in order; first match wins.
                            Handler receives (exception, tool_name) and returns list[TextContent].
        """
        self._startup_hook = startup_hook
        self._health_check = health_check
        self._error_handlers = error_handlers or []
        self.server = Server(self.server_name)
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return self.get_tools()

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            return await self._handle_tool_call(name, arguments)

    async def _handle_tool_call(self, name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle a tool call with consistent error handling."""
        try:
            result = self.handle_tool(name, arguments)
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            # Check custom error handlers first
            for exc_type, handler in self._error_handlers:
                if isinstance(e, exc_type):
                    return handler(e, name)

            # Default: log and return generic error
            logger.exception(f"Unexpected error in tool {name}")
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": f"Internal error: {e!s}",
                        }
                    ),
                )
            ]

    @abstractmethod
    def get_tools(self) -> list[Tool]:
        """Return list of tools provided by this server.

        Must be implemented by subclasses.
        """
        ...

    @abstractmethod
    def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle a tool call and return result.

        Must be implemented by subclasses.

        Args:
            name: The tool name
            arguments: Tool arguments from the client

        Returns:
            Dict with 'success' key and either result data or 'error' key
        """
        ...

    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(description=self.server_description)

        if self._health_check is not None:
            parser.add_argument("--health-check", action="store_true", help="Run health check and exit")

        if self._startup_hook is not None:
            parser.add_argument(
                "--skip-startup-hook",
                action="store_true",
                help="Skip startup hook execution",
            )

        return parser.parse_args()

    def run(self) -> None:
        """Run the MCP server."""
        args = self.parse_args()

        # Health check mode
        if self._health_check is not None and getattr(args, "health_check", False):
            sys.exit(self._health_check())

        logger.info(f"{self.server_name} MCP server starting...")

        # Run startup hook (unless skipped)
        if self._startup_hook is not None and not getattr(args, "skip_startup_hook", False):
            try:
                self._startup_hook()
                logger.info("Startup hook completed")
            except Exception:
                logger.exception("Startup hook failed")
                raise

        # Run the server
        async def main() -> None:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options(),
                )

        asyncio.run(main())
