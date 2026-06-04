"""Execution-lifecycle logging methods for :class:`MaivnLogger`.

Covers system startup, execution highlights, and agent/node lifecycle
events. These render with extra console formatting (centered headers,
colorized markers) compared to standard level methods.
"""

# pyright: strict
from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .config import SYSTEM_EVENTS, LogLevel
from .formatters import ColorFormatter, LogStyles, TextFormatter, resolve_log_style
from .writers import LogWriter

# MARK: MaivnLoggerExecutionMixin


class MaivnLoggerExecutionMixin:
    """Highlighted lifecycle logging (system startup, agent and node spans).

    Assumes the concrete class provides ``_writer``, ``_use_colors``,
    ``_should_log_to_console``, and ``_write_structured_log``.
    """

    if TYPE_CHECKING:
        _writer: LogWriter = cast(LogWriter, cast(object, None))
        _use_colors: bool = False

        def _should_log_to_console(self, level: LogLevel) -> bool:
            del level
            raise NotImplementedError

        def _write_structured_log(
            self,
            level: LogLevel,
            component: str,
            event: str,
            data: dict[str, object],
        ) -> None:
            del level, component, event, data
            raise NotImplementedError

    # MARK: - System Startup

    def log_system_startup(self) -> None:
        """Emit the highlighted startup banner for the platform logger."""
        file_status = "enabled" if self._writer.file_logging_enabled else "disabled"
        startup_msg = f"Maivn logger initialized (file_logging={file_status}"
        if self._writer.file_logging_enabled:
            startup_msg += f", log_file={self._writer.log_file}"
        startup_msg += ")"
        self.log_execution_highlight("SYSTEM", "STARTUP", startup_msg)

    def log_execution_highlight(
        self,
        component: str,
        event: str,
        message: str,
        **metadata: object,
    ) -> None:
        """Log a major execution checkpoint with highlighted console formatting."""
        is_system_event = component.upper() == "SYSTEM" and event in SYSTEM_EVENTS
        console_msg = self._format_execution_console_message(
            component, event, message, is_system_event
        )

        if self._should_log_to_console("INFO") and console_msg:
            self._writer.write_to_console(console_msg + "\n")

        self._write_structured_log(
            level="INFO",
            component=component,
            event=f"execution_{event.lower()}",
            data={"message": message, **metadata},
        )

    def _format_execution_console_message(
        self,
        component: str,
        event: str,
        message: str,
        is_system_event: bool,
    ) -> str:
        """Render the colorized console line for an execution-highlight event."""
        if is_system_event:
            return ""

        if self._use_colors:
            event_colored = ColorFormatter.colorize_text(event, LogStyles.EXECUTION_HIGHLIGHT)
            component_colored = ColorFormatter.colorize_text(
                component, resolve_log_style(component.upper())
            )
            return f"{event_colored} {component_colored} {message}"

        return f"[{event}] [{component}] {message}"

    # MARK: - Agent Invocation

    def log_agent_invocation_start(self, agent_name: str, **metadata: object) -> None:
        """Log the start of an agent invocation."""
        message = f"Agent '{agent_name}' invocation started"
        self.log_execution_highlight(
            "AGENT", "INVOCATION_START", message, agent_name=agent_name, **metadata
        )

    def log_agent_invocation_end(
        self,
        agent_name: str,
        duration_ms: int | None = None,
        **metadata: object,
    ) -> None:
        """Log the end of an agent invocation, optionally with duration."""
        message = f"Agent '{agent_name}' invocation completed"
        if duration_ms is not None:
            message += f" ({duration_ms}ms)"
        self.log_execution_highlight(
            "AGENT",
            "INVOCATION_END",
            message,
            agent_name=agent_name,
            duration_ms=duration_ms,
            **metadata,
        )

    # MARK: - Node Execution

    def log_node_start(self, agent_name: str, node_name: str, **metadata: object) -> None:
        """Log the start of a node execution with a centered console header."""
        console_msg = self._format_node_start_header(agent_name, node_name)

        if self._should_log_to_console("INFO"):
            self._writer.write_to_console(console_msg)

        file_message = f"Node '{node_name}' in agent '{agent_name}' started"
        self._write_structured_log(
            level="INFO",
            component="NODE",
            event="node_start",
            data={
                "agent_name": agent_name,
                "node_name": node_name,
                "message": file_message,
                **metadata,
            },
        )

    def _format_node_start_header(self, agent_name: str, node_name: str) -> str:
        """Render the centered, padded console header for a node-start event."""
        header_text = f"{agent_name.upper()} - {node_name.upper()}"
        centered_header = TextFormatter.center_text(header_text, width=80, fill_char="-")

        if self._use_colors:
            colored_header = ColorFormatter.colorize_text(
                centered_header, LogStyles.EXECUTION_START
            )
            return f"\n{colored_header}\n"

        return f"\n{centered_header}\n"

    def log_node_end(
        self,
        agent_name: str,
        node_name: str,
        duration_ms: int | None = None,
        **metadata: object,
    ) -> None:
        """Log the end of a node execution, optionally with duration."""
        message = f"Node '{node_name}' in agent '{agent_name}' completed"
        if duration_ms is not None:
            message += f" ({duration_ms}ms)"

        self.log_execution_highlight(
            "NODE",
            "COMPLETION",
            message,
            agent_name=agent_name,
            node_name=node_name,
            duration_ms=duration_ms,
            **metadata,
        )


__all__ = ["MaivnLoggerExecutionMixin"]
