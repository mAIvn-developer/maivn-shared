"""Standard-level logging methods for :class:`MaivnLogger`.

Provided as a mixin so the concrete logger class declaration stays focused on
initialization and the low-level write path. ``log_custom`` is the single
choke point every level method funnels through (via ``_log_at_level``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import LogLevel


# MARK: MaivnLoggerLevelsMixin


class MaivnLoggerLevelsMixin:
    """Standard log-level methods (``debug``/``info``/``warning``/``error``/``critical``).

    Assumes the concrete class provides ``_write_structured_log``,
    ``_log_at_level``, and ``_truncate_message`` (all on :class:`MaivnLogger`).
    """

    # MARK: - Core

    def log_custom(
        self,
        level: LogLevel,
        component: str,
        message: str,
        **metadata: Any,
    ) -> None:
        """Log a message at ``level`` with arbitrary structured metadata."""
        self._write_structured_log(  # type: ignore[attr-defined]
            level=level,
            component=component,
            event="custom",
            data={"message": self._truncate_message(message), **metadata},  # type: ignore[attr-defined]
        )

    # MARK: - Standard Level Methods

    def debug(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """Log a debug message."""
        self._log_at_level("DEBUG", message, *args, component=component, **metadata)  # type: ignore[attr-defined]

    def info(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """Log an info message."""
        self._log_at_level("INFO", message, *args, component=component, **metadata)  # type: ignore[attr-defined]

    def warning(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """Log a warning message."""
        self._log_at_level("WARNING", message, *args, component=component, **metadata)  # type: ignore[attr-defined]

    def error(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """Log an error message."""
        self._log_at_level("ERROR", message, *args, component=component, **metadata)  # type: ignore[attr-defined]

    def critical(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """Log a critical message."""
        self._log_at_level("CRITICAL", message, *args, component=component, **metadata)  # type: ignore[attr-defined]

    # MARK: - Error Logging

    def log_error(
        self,
        component: str,
        error_type: str,
        error_message: str,
        stack_trace: str | None = None,
        **metadata: Any,
    ) -> None:
        """Log a structured error event including ``error_type`` and optional stack trace.

        Mirrors ``error_message`` into ``message`` so the rendered log line
        shows the actual error text rather than the generic
        ``"error event in <component>"`` fallback used by
        :func:`_write_structured_log` when ``data["message"]`` is missing.
        """
        self._write_structured_log(  # type: ignore[attr-defined]
            level="ERROR",
            component=component,
            event="error",
            data={
                "message": error_message,
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                **metadata,
            },
        )

    def exception(self, message: str, component: str = "APP", **metadata: Any) -> None:
        """Log an exception with the current traceback attached."""
        import traceback

        self.log_error(
            component=component,
            error_type="Exception",
            error_message=message,
            stack_trace=traceback.format_exc(),
            **metadata,
        )


__all__ = ["MaivnLoggerLevelsMixin"]
