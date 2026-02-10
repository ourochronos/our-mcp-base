"""oro-mcp-base -- MCP server base framework for the ourochronos ecosystem.

Provides MCPServerBase, ToolRouter, and response helpers for building
MCP servers with consistent patterns.
"""

__version__ = "0.1.0"

from .responses import error_response, not_found_response, success_response
from .router import ToolRouter
from .server import MCPServerBase

__all__ = [
    "MCPServerBase",
    "ToolRouter",
    "error_response",
    "not_found_response",
    "success_response",
]
