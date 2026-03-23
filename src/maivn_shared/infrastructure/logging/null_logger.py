"""Null logger implementation (Null Object pattern).

This module provides a NullLogger that implements the logger interface
but performs no operations, allowing code to call logging methods without
None checks.
"""

from __future__ import annotations

from typing import Any


class NullLogger:
    """Null logger that does nothing (Null Object pattern).

    This logger is returned by get_optional_logger() when the actual logger
    is unavailable, allowing code to call logging methods without None checks.
    """

    # MARK: - Context Management

    def set_context(self, **kwargs: Any) -> None:
        """No-op context setting."""

    def clear_context(self, *keys: str) -> None:
        """No-op context clearing."""

    # MARK: - Standard Logging Methods

    def log_custom(self, level: str, component: str, message: str, **metadata: Any) -> None:
        """No-op custom logging."""

    def debug(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """No-op debug logging."""

    def info(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """No-op info logging."""

    def warning(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """No-op warning logging."""

    def error(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """No-op error logging."""

    def critical(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """No-op critical logging."""

    # MARK: - Error Logging

    def log_error(
        self,
        component: str,
        error_type: str,
        error_message: str,
        stack_trace: str | None = None,
        **metadata: Any,
    ) -> None:
        """No-op structured error logging."""

    def exception(self, message: str, component: str = "APP", **metadata: Any) -> None:
        """No-op exception logging."""

    # MARK: - Metrics Logging

    def log_token_usage(self, *args: Any, **kwargs: Any) -> None:
        """No-op token usage logging."""

    def log_tool_execution(self, *args: Any, **kwargs: Any) -> None:
        """No-op tool execution logging."""

    # MARK: - Execution Logging

    def log_system_startup(self) -> None:
        """No-op system startup logging."""

    def log_execution_highlight(
        self, component: str, event: str, message: str, **metadata: Any
    ) -> None:
        """No-op execution highlight logging."""

    # MARK: - Agent Logging

    def log_agent_invocation_start(self, agent_name: str, **metadata: Any) -> None:
        """No-op agent invocation start logging."""

    def log_agent_invocation_end(
        self, agent_name: str, duration_ms: int | None = None, **metadata: Any
    ) -> None:
        """No-op agent invocation end logging."""

    # MARK: - Node Logging

    def log_node_start(self, agent_name: str, node_name: str, **metadata: Any) -> None:
        """No-op node start logging."""

    def log_node_end(
        self, agent_name: str, node_name: str, duration_ms: int | None = None, **metadata: Any
    ) -> None:
        """No-op node end logging."""
