"""Structural-typing protocols for the maivn logger surface.

These ``Protocol`` classes describe the minimum logger interface consumers
can depend on without importing :class:`MaivnLogger` directly. They let
non-SDK code accept any object that quacks like a logger (real loggers,
test fakes, the null logger) and stay type-checked.
"""

from __future__ import annotations

from typing import Any, Literal, Protocol


class LoggerProtocol(Protocol):
    """Minimum logger surface: the five standard log levels plus ``exception``.

    A :class:`logging.Logger`, :class:`MaivnLogger`, or any test stub that
    declares these methods satisfies this protocol.
    """

    def debug(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None: ...

    def info(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None: ...

    def warning(
        self, message: str, *args: Any, component: str = "APP", **metadata: Any
    ) -> None: ...

    def error(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None: ...

    def exception(self, message: str, component: str = "APP", **metadata: Any) -> None: ...

    def critical(
        self, message: str, *args: Any, component: str = "APP", **metadata: Any
    ) -> None: ...


class MetricsLoggerProtocol(LoggerProtocol, Protocol):
    """Logger that also records structured tool-execution and token-usage metrics.

    Extends :class:`LoggerProtocol` with the two structured-emission methods
    the SDK uses to track per-tool timing and per-invocation token costs.
    Implementations that don't want metrics can implement these as no-ops.
    """

    def log_tool_execution(
        self,
        phase: Literal["start", "completed", "failed"],
        tool_id: str,
        tool_name: str,
        tool_type: str | None = None,
        args: dict[str, Any] | None = None,
        result: Any = None,
        error: str | None = None,
        elapsed_ms: int | None = None,
        session_id: str | None = None,
        thread_id: str | None = None,
        task_idx: int | None = None,
        **metadata: Any,
    ) -> None: ...

    def log_token_usage(
        self,
        agent_name: str,
        invocation_type: str,
        total_tokens: int,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
        model: str = "unknown",
        provider: str = "unknown",
        total_cost: float = 0.0,
        session_id: str | None = None,
        thread_id: str | None = None,
        batch_number: int | None = None,
        **metadata: Any,
    ) -> None: ...


__all__ = ["LoggerProtocol", "MetricsLoggerProtocol"]
