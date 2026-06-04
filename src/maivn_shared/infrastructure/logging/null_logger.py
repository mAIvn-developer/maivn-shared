"""Null logger implementation (Null Object pattern).

This module provides a NullLogger that implements the logger interface
but performs no operations, allowing code to call logging methods without
None checks.
"""

# pyright: strict
from __future__ import annotations


class NullLogger:
    """Null logger that does nothing (Null Object pattern).

    This logger is returned by get_optional_logger() when the actual logger
    is unavailable, allowing code to call logging methods without None checks.
    """

    # MARK: - Context Management

    def set_context(self, **kwargs: object) -> None:
        """No-op context setting."""
        del kwargs

    def clear_context(self, *keys: str) -> None:
        """No-op context clearing."""
        del keys

    # MARK: - Standard Logging Methods

    def log_custom(self, level: str, component: str, message: str, **metadata: object) -> None:
        """No-op custom logging."""
        del level, component, message, metadata

    def debug(
        self, message: str, *args: object, component: str = "APP", **metadata: object
    ) -> None:
        """No-op debug logging."""
        del message, args, component, metadata

    def info(self, message: str, *args: object, component: str = "APP", **metadata: object) -> None:
        """No-op info logging."""
        del message, args, component, metadata

    def warning(
        self, message: str, *args: object, component: str = "APP", **metadata: object
    ) -> None:
        """No-op warning logging."""
        del message, args, component, metadata

    def error(
        self, message: str, *args: object, component: str = "APP", **metadata: object
    ) -> None:
        """No-op error logging."""
        del message, args, component, metadata

    def critical(
        self, message: str, *args: object, component: str = "APP", **metadata: object
    ) -> None:
        """No-op critical logging."""
        del message, args, component, metadata

    # MARK: - Error Logging

    def log_error(
        self,
        component: str,
        error_type: str,
        error_message: str,
        stack_trace: str | None = None,
        **metadata: object,
    ) -> None:
        """No-op structured error logging."""
        del component, error_type, error_message, stack_trace, metadata

    def exception(self, message: str, component: str = "APP", **metadata: object) -> None:
        """No-op exception logging."""
        del message, component, metadata

    # MARK: - Metrics Logging

    def log_token_usage(self, *args: object, **kwargs: object) -> None:
        """No-op token usage logging."""
        del args, kwargs

    def log_tool_execution(self, *args: object, **kwargs: object) -> None:
        """No-op tool execution logging."""
        del args, kwargs

    # MARK: - Execution Logging

    def log_system_startup(self) -> None:
        """No-op system startup logging."""

    def log_execution_highlight(
        self, component: str, event: str, message: str, **metadata: object
    ) -> None:
        """No-op execution highlight logging."""
        del component, event, message, metadata

    # MARK: - Agent Logging

    def log_agent_invocation_start(self, agent_name: str, **metadata: object) -> None:
        """No-op agent invocation start logging."""
        del agent_name, metadata

    def log_agent_invocation_end(
        self, agent_name: str, duration_ms: int | None = None, **metadata: object
    ) -> None:
        """No-op agent invocation end logging."""
        del agent_name, duration_ms, metadata

    # MARK: - Node Logging

    def log_node_start(self, agent_name: str, node_name: str, **metadata: object) -> None:
        """No-op node start logging."""
        del agent_name, node_name, metadata

    def log_node_end(
        self, agent_name: str, node_name: str, duration_ms: int | None = None, **metadata: object
    ) -> None:
        """No-op node end logging."""
        del agent_name, node_name, duration_ms, metadata
