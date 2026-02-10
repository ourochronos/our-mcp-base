# our-mcp-base

Base framework for building MCP (Model Context Protocol) servers in the ourochronos ecosystem.

## Overview

our-mcp-base provides reusable patterns for MCP server implementations: an abstract base class with lifecycle hooks, a decorator-based tool router, and consistent response formatting. It reduces boilerplate and ensures all MCP servers in the ecosystem follow the same conventions.

## Install

```bash
pip install our-mcp-base
```

Requires `mcp>=1.0`.

## Usage

### Basic Server

```python
from mcp.types import Tool
from our_mcp_base import MCPServerBase

class MyServer(MCPServerBase):
    server_name = "my-server"

    def get_tools(self) -> list[Tool]:
        return [
            Tool(name="greet", description="Say hello", inputSchema={...}),
        ]

    def handle_tool(self, name: str, arguments: dict) -> dict:
        if name == "greet":
            return {"success": True, "message": f"Hello, {arguments['name']}!"}
        return {"success": False, "error": f"Unknown tool: {name}"}

if __name__ == "__main__":
    MyServer().run()
```

### With Lifecycle Hooks

```python
MyServer(
    startup_hook=lambda: init_database(),
    health_check=lambda: check_db_connection(),
).run()
```

Run with `--health-check` to execute the health check and exit, or `--skip-startup-hook` to skip initialization.

### Tool Router

```python
from our_mcp_base import ToolRouter

router = ToolRouter()

@router.register("greet")
def handle_greet(name: str, enthusiasm: int = 1) -> dict:
    return {"success": True, "message": f"Hello, {name}{'!' * enthusiasm}"}

# In handle_tool:
result = router.dispatch(name, arguments)
```

### Response Helpers

```python
from our_mcp_base import success_response, error_response, not_found_response

success_response(data="value", count=42)
# → {"success": True, "data": "value", "count": 42}

error_response("Invalid input", code=400)
# → {"success": False, "error": "Invalid input", "code": 400}

not_found_response("Belief", "belief-123")
# → {"success": False, "error": "Belief not found: belief-123"}
```

### Custom Error Handling

```python
def handle_db_error(exc: Exception, tool_name: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"success": False, "error": str(exc)}))]

server = MyServer(error_handlers=[(DatabaseError, handle_db_error)])
```

## API

| Symbol | Description |
|--------|-------------|
| `MCPServerBase` | Abstract base class — implement `get_tools()` and `handle_tool()` |
| `ToolRouter` | Decorator-based tool dispatch registry |
| `success_response(**kwargs)` | Returns `{success: True, ...}` |
| `error_response(error, **kwargs)` | Returns `{success: False, error: str, ...}` |
| `not_found_response(type, id)` | Returns a 404-style error response |

## Development

```bash
# Install with dev dependencies
make dev

# Run linters
make lint

# Run tests
make test

# Run tests with coverage
make test-cov

# Auto-format
make format
```

## State Ownership

None. This package provides base classes and utilities only. State is owned by the concrete MCP server implementations that inherit from `MCPServerBase`.

## Part of Valence

This brick is part of the [Valence](https://github.com/ourochronos/valence) knowledge substrate. See [our-infra](https://github.com/ourochronos/our-infra) for ourochronos conventions.

## License

MIT
