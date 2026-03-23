"""Context management for logger.

This module provides thread-safe context tracking for logger instances.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

# MARK: - Context Manager


class ContextManager:
    """Manages thread-safe context storage for logging.

    Context data is shared across all log calls in the same thread/session,
    allowing consistent metadata to be attached to log entries.
    """

    # MARK: - Initialization

    def __init__(self) -> None:
        """Initialize the context manager."""
        self._context_var: ContextVar[dict[str, Any] | None] = ContextVar(
            "maivn_logger_context",
            default=None,
        )

    # MARK: - Context Operations

    def set(self, **kwargs: Any) -> None:
        """Set context values for all subsequent logs.

        Args:
            **kwargs: Context key-value pairs (e.g., session_id, thread_id)
        """
        current = self._context_var.get() or {}
        self._context_var.set({**current, **kwargs})

    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific context value.

        Args:
            key: Context key to retrieve
            default: Default value if key not found

        Returns:
            Context value or default
        """
        return (self._context_var.get() or {}).get(key, default)

    def clear(self, *keys: str) -> None:
        """Clear specific context keys or all context if no keys provided.

        Args:
            *keys: Context keys to clear (clears all if empty)
        """
        current = self._context_var.get() or {}
        if not keys:
            self._context_var.set(None)
            return

        updated = dict(current)
        for key in keys:
            updated.pop(key, None)
        self._context_var.set(updated)

    # MARK: - Context Retrieval

    def get_context(self) -> dict[str, Any]:
        """Get a copy of the current context.

        Returns:
            Dictionary containing current context data
        """
        return dict(self._context_var.get() or {})

    def has_context(self) -> bool:
        """Check if any context data exists.

        Returns:
            True if context is not empty
        """
        return bool(self._context_var.get())
