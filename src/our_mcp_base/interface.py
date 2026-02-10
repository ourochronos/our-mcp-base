"""Public interface for our-mcp-base.

Re-exports the abstract base class that forms this brick's public contract.
The MCPServerBase ABC defines the interface that all MCP servers must implement.
"""

from .server import MCPServerBase

__all__ = ["MCPServerBase"]
