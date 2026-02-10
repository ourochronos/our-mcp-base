"""Response helpers for MCP tool handlers.

Provides consistent response formatting for success, error, and not-found cases.
All responses follow the {success: bool, ...data} convention.
"""

from __future__ import annotations

from typing import Any


def success_response(**kwargs: Any) -> dict[str, Any]:
    """Create a successful response dict.

    Args:
        **kwargs: Additional data to include in response

    Returns:
        Dict with success=True and all kwargs
    """
    return {"success": True, **kwargs}


def error_response(error: str, **kwargs: Any) -> dict[str, Any]:
    """Create an error response dict.

    Args:
        error: Error message
        **kwargs: Additional data to include in response

    Returns:
        Dict with success=False, error message, and all kwargs
    """
    return {"success": False, "error": error, **kwargs}


def not_found_response(resource_type: str, resource_id: str) -> dict[str, Any]:
    """Create a not found error response.

    Args:
        resource_type: Type of resource (e.g., "Belief", "User")
        resource_id: ID of the missing resource

    Returns:
        Dict with success=False and appropriate error message
    """
    return error_response(f"{resource_type} not found: {resource_id}")
