"""Standard-level logging methods for :class:`MaivnLogger`.

Provided as a mixin so the concrete logger class declaration stays focused on
initialization and the low-level write path. ``log_custom`` is the single
choke point every level method funnels through (via ``_log_at_level``).
"""

# pyright: strict
from __future__ import annotations

from typing import TYPE_CHECKING

from .config import LogLevel

# MARK: MaivnLoggerLevelsMixin


class MaivnLoggerLevelsMixin:
    """Standard log-level methods (``debug``/``info``/``warning``/``error``/``critical``).

    Assumes the concrete class provides ``_write_structured_log`` and
    ``_log_at_level`` (both on :class:`MaivnLogger`).
    """

    if TYPE_CHECKING:

        def _write_structured_log(
            self,
            level: LogLevel,
            component: str,
            event: str,
            data: dict[str, object],
        ) -> None:
            del level, component, event, data
            raise NotImplementedError

        def _log_at_level(
            self,
            level: LogLevel,
            message: str,
            *args: object,
            component: str,
            **metadata: object,
        ) -> None:
            del level, message, args, component, metadata
            raise NotImplementedError

    # MARK: - Core

    def log_custom(
        self,
        level: LogLevel,
        component: str,
        message: str,
        **metadata: object,
    ) -> None:
        """Log a message at ``level`` with arbitrary structured metadata.

        The message is *not* truncated here: ``_write_structured_log`` clamps
        the rendered message to ``_max_message_length`` at the single canonical
        boundary, so truncating again at this entry point would be redundant.
        """
        self._write_structured_log(
            level=level,
            component=component,
            event="custom",
            data={"message": message, **metadata},
        )

    # MARK: - Standard Level Methods

    def debug(
        self,
        message: str,
        *args: object,
        component: str = "APP",
        **metadata: object,
    ) -> None:
        """Log a debug message."""
        self._log_at_level("DEBUG", message, *args, component=component, **metadata)

    def info(
        self,
        message: str,
        *args: object,
        component: str = "APP",
        **metadata: object,
    ) -> None:
        """Log an info message."""
        self._log_at_level("INFO", message, *args, component=component, **metadata)

    def warning(
        self,
        message: str,
        *args: object,
        component: str = "APP",
        **metadata: object,
    ) -> None:
        """Log a warning message."""
        self._log_at_level("WARNING", message, *args, component=component, **metadata)

    def error(
        self,
        message: str,
        *args: object,
        component: str = "APP",
        **metadata: object,
    ) -> None:
        """Log an error message."""
        self._log_at_level("ERROR", message, *args, component=component, **metadata)

    def critical(
        self,
        message: str,
        *args: object,
        component: str = "APP",
        **metadata: object,
    ) -> None:
        """Log a critical message."""
        self._log_at_level("CRITICAL", message, *args, component=component, **metadata)

    # MARK: - Error Logging

    def log_error(
        self,
        component: str,
        error_type: str,
        error_message: str,
        stack_trace: str | None = None,
        **metadata: object,
    ) -> None:
        """Log a structured error event including ``error_type`` and optional stack trace.

        Mirrors ``error_message`` into ``message`` so the rendered log line
        shows the actual error text rather than the generic
        ``"error event in <component>"`` fallback used by
        :func:`_write_structured_log` when ``data["message"]`` is missing.
        """
        self._write_structured_log(
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

    def exception(self, message: str, component: str = "APP", **metadata: object) -> None:
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
