"""Tests for oro_mcp_base.responses module."""

from __future__ import annotations

from oro_mcp_base.responses import error_response, not_found_response, success_response


class TestSuccessResponse:
    """Tests for success_response helper function."""

    def test_basic_success(self) -> None:
        """Should return success=True."""
        result = success_response()
        assert result["success"] is True

    def test_with_kwargs(self) -> None:
        """Should include additional kwargs."""
        result = success_response(data="test", count=42)
        assert result["success"] is True
        assert result["data"] == "test"
        assert result["count"] == 42

    def test_with_nested_data(self) -> None:
        """Should handle nested data."""
        result = success_response(
            item={"id": "123", "content": "test"},
            items=[{"name": "Item1"}],
        )
        assert result["success"] is True
        assert result["item"]["id"] == "123"
        assert len(result["items"]) == 1


class TestErrorResponse:
    """Tests for error_response helper function."""

    def test_basic_error(self) -> None:
        """Should return success=False with error message."""
        result = error_response("Something went wrong")
        assert result["success"] is False
        assert result["error"] == "Something went wrong"

    def test_with_kwargs(self) -> None:
        """Should include additional kwargs."""
        result = error_response("Failed", code=404, details={"field": "id"})
        assert result["success"] is False
        assert result["error"] == "Failed"
        assert result["code"] == 404
        assert result["details"]["field"] == "id"


class TestNotFoundResponse:
    """Tests for not_found_response helper function."""

    def test_creates_not_found_error(self) -> None:
        """Should create appropriate not found message."""
        result = not_found_response("User", "abc-123")
        assert result["success"] is False
        assert "User not found" in result["error"]
        assert "abc-123" in result["error"]

    def test_different_resource_types(self) -> None:
        """Should work with different resource types."""
        result1 = not_found_response("Entity", "entity-1")
        assert "Entity not found" in result1["error"]

        result2 = not_found_response("Session", "session-2")
        assert "Session not found" in result2["error"]
