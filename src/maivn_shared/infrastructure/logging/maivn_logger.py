"""Maivn platform logger - consolidated logging implementation.

This module provides MaivnLogger with all logging functionality:
- Standard log levels (debug, info, warning, error, critical)
- Context management
- Execution logging (agents, nodes)
- Metrics logging (token usage, tool execution)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from .config import (
    DEFAULT_CONSOLE_LEVEL,
    DEFAULT_FILE_LEVEL,
    DEFAULT_HUMAN_READABLE_CONSOLE,
    DEFAULT_MAX_COLLECTION_ITEMS,
    DEFAULT_MAX_MESSAGE_LENGTH,
    DEFAULT_MAX_STRING_LENGTH,
    DEFAULT_USE_COLORS,
    LOG_LEVEL_PRIORITY,
    SYSTEM_EVENTS,
    LogLevel,
)
from .context import ContextManager
from .formatters import (
    ColorFormatter,
    HumanReadableFormatter,
    JSONFormatter,
    LogStyles,
    TextFormatter,
    TimestampFormatter,
)
from .writers import LogWriter


class MaivnLogger:
    """Main Maivn platform logger with full functionality.

    Provides:
    - Standard log levels (debug, info, warning, error, critical)
    - Context management
    - Structured JSON logging
    - Console and file output
    - Agent and node execution logging
    - Token usage and tool execution logging
    """

    # MARK: Initialization

    def __init__(
        self,
        log_file_path: Path | str | None = None,
        console_level: LogLevel = DEFAULT_CONSOLE_LEVEL,
        file_level: LogLevel = DEFAULT_FILE_LEVEL,
        use_colors: bool = DEFAULT_USE_COLORS,
        human_readable_console: bool = DEFAULT_HUMAN_READABLE_CONSOLE,
    ) -> None:
        """Initialize the Maivn logger.

        Args:
            log_file_path: Full path to log file (None disables file logging)
            console_level: Minimum log level for console output (default: OFF = no console)
            file_level: Minimum log level for file output (default: INFO)
            use_colors: Whether to use colors in console output
            human_readable_console: Whether to use human-readable format for console
        """
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._use_colors = use_colors
        self._human_readable_console = human_readable_console
        self._console_level = console_level
        self._file_level = file_level
        self._level_priority = LOG_LEVEL_PRIORITY
        self._context_manager = ContextManager()
        self._writer = self._create_writer(log_file_path)
        self._max_message_length = max(64, DEFAULT_MAX_MESSAGE_LENGTH)
        self._max_string_length = max(64, DEFAULT_MAX_STRING_LENGTH)
        self._max_collection_items = max(1, DEFAULT_MAX_COLLECTION_ITEMS)
        self._startup_logged = False
        self._log_startup_once()

    def _create_writer(self, log_file_path: Path | str | None) -> LogWriter:
        """Create and configure the log writer."""
        log_file = Path(log_file_path) if log_file_path else None
        if log_file:
            log_file.parent.mkdir(exist_ok=True, parents=True)
        return LogWriter(log_file)

    def _log_startup_once(self) -> None:
        """Log system startup exactly once after successful initialization."""
        if self._initialized and not self._startup_logged:
            self._startup_logged = True
            self.log_system_startup()

    # MARK: Context Management

    def set_context(self, **kwargs: Any) -> None:
        """Set context values for all subsequent logs."""
        self._context_manager.set(**kwargs)

    def clear_context(self, *keys: str) -> None:
        """Clear specific context keys or all context if no keys provided."""
        self._context_manager.clear(*keys)

    def get_context(self) -> dict[str, Any]:
        """Get a copy of the active logging context for the current execution context."""
        return self._context_manager.get_context()

    # MARK: Core Logging Methods

    def log_custom(
        self,
        level: LogLevel,
        component: str,
        message: str,
        **metadata: Any,
    ) -> None:
        """Log custom message with metadata."""
        self._write_structured_log(
            level=level,
            component=component,
            event="custom",
            data={"message": self._truncate_message(message), **metadata},
        )

    # MARK: - Standard Level Methods

    def debug(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """Log debug message."""
        self._log_at_level("DEBUG", message, *args, component=component, **metadata)

    def info(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """Log info message."""
        self._log_at_level("INFO", message, *args, component=component, **metadata)

    def warning(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """Log warning message."""
        self._log_at_level("WARNING", message, *args, component=component, **metadata)

    def error(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """Log error message."""
        self._log_at_level("ERROR", message, *args, component=component, **metadata)

    def critical(self, message: str, *args: Any, component: str = "APP", **metadata: Any) -> None:
        """Log critical message."""
        self._log_at_level("CRITICAL", message, *args, component=component, **metadata)

    # MARK: - Error Logging

    def log_error(
        self,
        component: str,
        error_type: str,
        error_message: str,
        stack_trace: str | None = None,
        **metadata: Any,
    ) -> None:
        """Log error with full context and structured data."""
        self._write_structured_log(
            level="ERROR",
            component=component,
            event="error",
            data={
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                **metadata,
            },
        )

    def exception(self, message: str, component: str = "APP", **metadata: Any) -> None:
        """Log exception with stack trace."""
        import traceback

        self.log_error(
            component=component,
            error_type="Exception",
            error_message=message,
            stack_trace=traceback.format_exc(),
            **metadata,
        )

    # MARK: Execution Logging

    def log_system_startup(self) -> None:
        """Log system startup with highlighted formatting."""
        file_status = "enabled" if self._writer.file_logging_enabled else "disabled"
        startup_msg = f"Maivn logger initialized (file_logging={file_status}"
        if self._writer.file_logging_enabled:
            startup_msg += f", log_file={self._writer.log_file}"
        startup_msg += ")"
        self.log_execution_highlight("SYSTEM", "STARTUP", startup_msg)

    def log_execution_highlight(
        self, component: str, event: str, message: str, **metadata: Any
    ) -> None:
        """Log major execution points with enhanced formatting."""
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
        self, component: str, event: str, message: str, is_system_event: bool
    ) -> str:
        """Format console message for execution highlights."""
        if is_system_event:
            return ""

        if self._use_colors:
            event_colored = ColorFormatter.colorize_text(event, LogStyles.EXECUTION_HIGHLIGHT)
            component_colored = ColorFormatter.colorize_text(
                component, LogStyles.__dict__.get(component.upper(), ColorFormatter.WHITE)
            )
            return f"{event_colored} {component_colored} {message}"

        return f"[{event}] [{component}] {message}"

    # MARK: - Agent Invocation

    def log_agent_invocation_start(self, agent_name: str, **metadata: Any) -> None:
        """Log the start of an agent invocation with highlighted formatting."""
        message = f"Agent '{agent_name}' invocation started"
        self.log_execution_highlight(
            "AGENT", "INVOCATION_START", message, agent_name=agent_name, **metadata
        )

    def log_agent_invocation_end(
        self, agent_name: str, duration_ms: int | None = None, **metadata: Any
    ) -> None:
        """Log the end of an agent invocation with highlighted formatting."""
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

    def log_node_start(self, agent_name: str, node_name: str, **metadata: Any) -> None:
        """Log the start of a node execution with centered, highlighted formatting."""
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
        """Format the centered header for node start."""
        header_text = f"{agent_name.upper()} - {node_name.upper()}"
        centered_header = TextFormatter.center_text(header_text, width=80, fill_char="-")

        if self._use_colors:
            colored_header = ColorFormatter.colorize_text(
                centered_header, LogStyles.EXECUTION_START
            )
            return f"\n{colored_header}\n"

        return f"\n{centered_header}\n"

    def log_node_end(
        self, agent_name: str, node_name: str, duration_ms: int | None = None, **metadata: Any
    ) -> None:
        """Log the end of a node execution."""
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

    # MARK: Metrics Logging

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
    ) -> None:
        """Log token usage with full cost details (file only, not console)."""
        if not self._writer.file_logging_enabled:
            return

        cache_hit_rate = (cache_read_tokens / input_tokens * 100) if input_tokens > 0 else 0
        non_cached_input = input_tokens - cache_read_tokens

        data: dict[str, Any] = {
            "agent_name": agent_name,
            "invocation_type": invocation_type,
            "model": model,
            "provider": provider,
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_tokens": cache_read_tokens,
            "cache_creation_tokens": cache_creation_tokens,
            "non_cached_input_tokens": non_cached_input,
            "cache_hit_rate_pct": round(cache_hit_rate, 1),
            "total_cost_usd": round(total_cost, 6),
        }

        if session_id:
            data["session_id"] = session_id
        if thread_id:
            data["thread_id"] = thread_id
        if batch_number is not None:
            data["batch_number"] = batch_number

        data.update(metadata)

        self._write_structured_log(
            level="INFO",
            component="TOKEN_USAGE",
            event="token_usage",
            data=data,
        )

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
    ) -> None:
        """Log tool execution details (both console and file)."""
        level: LogLevel = "ERROR" if phase == "failed" else "INFO"

        data: dict[str, Any] = {
            "tool_id": tool_id,
            "tool_name": tool_name,
            "tool_type": tool_type,
            "phase": phase,
            "elapsed_ms": elapsed_ms,
        }

        if session_id:
            data["session_id"] = session_id
        if thread_id:
            data["thread_id"] = thread_id
        if task_idx is not None:
            data["task_idx"] = task_idx
        if args:
            data["args_keys"] = list(args.keys())
        if result is not None:
            result_str = str(result)
            data["result_preview"] = result_str[:200] if len(result_str) > 200 else result_str
        if error:
            data["error"] = error

        data.update(metadata)

        self._write_structured_log(
            level=level,
            component="TOOL_EXECUTION",
            event=f"tool_{phase}",
            data=data,
        )

    # MARK: Internal Methods

    def _should_log_to_console(self, level: LogLevel) -> bool:
        """Check if a log level should be output to console."""
        return self._level_priority[level] >= self._level_priority[self._console_level]

    def _should_log_to_file(self, level: LogLevel) -> bool:
        """Check if a log level should be written to file."""
        return self._level_priority[level] >= self._level_priority[self._file_level]

    def _log_at_level(
        self, level: LogLevel, message: str, *args: Any, component: str, **metadata: Any
    ) -> None:
        """Log message at specified level with optional formatting."""
        formatted_message = message % args if args else message
        self.log_custom(level=level, component=component, message=formatted_message, **metadata)

    def _write_structured_log(
        self,
        level: LogLevel,
        component: str,
        event: str,
        data: dict[str, Any],
    ) -> None:
        """Write a structured log entry."""
        sanitized_data = self._sanitize_mapping(data)
        entry = self._build_log_entry(level, component, event, sanitized_data)
        to_console = self._should_log_to_console(level)
        to_file = self._writer.file_logging_enabled and self._should_log_to_file(level)
        message_value = sanitized_data.get("message")
        message = (
            self._truncate_message(message_value)
            if isinstance(message_value, str)
            else self._truncate_message(f"{event} event in {component}")
        )

        console_line = (
            self._format_console_line(entry, level, component, message) if to_console else ""
        )
        file_line = self._format_file_line(entry, level, component, message) if to_file else ""

        self._writer.write_dual(console_line, file_line, to_console)

    def _build_log_entry(
        self, level: LogLevel, component: str, event: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Build structured log entry dictionary."""
        entry: dict[str, Any] = {
            "timestamp": TimestampFormatter.format_timestamp(),
            "level": level,
            "component": component,
            "event": event,
        }

        if self._context_manager.has_context():
            entry["context"] = self._sanitize_mapping(self._context_manager.get_context())

        if data:
            entry["data"] = data

        return entry

    def _format_console_line(
        self, entry: dict[str, Any], level: LogLevel, component: str, message: str
    ) -> str:
        """Format log entry for console output."""
        if self._human_readable_console:
            return (
                HumanReadableFormatter.format_readable_log_message(
                    level, component, message, self._use_colors
                )
                + "\n"
            )
        return JSONFormatter.safe_json_dumps(entry) + "\n"

    def _format_file_line(
        self,
        entry: dict[str, Any],
        level: LogLevel,
        component: str,
        message: str,
    ) -> str:
        """Format log entry for file output."""
        if not self._writer.file_logging_enabled:
            return ""

        context_tokens = self._extract_correlation_tokens(entry)
        if context_tokens:
            message = f"{message} [{context_tokens}]"

        message = self._truncate_message(message)

        return HumanReadableFormatter.format_log_line(
            str(entry.get("timestamp", TimestampFormatter.format_timestamp())),
            level,
            component,
            message,
        )

    def _extract_correlation_tokens(self, entry: dict[str, Any]) -> str:
        """Extract compact correlation fields for file logs."""
        context = entry.get("context")
        data = entry.get("data")
        context_map = context if isinstance(context, dict) else {}
        data_map = data if isinstance(data, dict) else {}

        keys = (
            "session_id",
            "user_id",
            "project_id",
            "user_thread_id",
            "thread_id",
            "request_id",
            "checkpoint_id",
            "invocation_id",
            "tool_event_id",
        )
        tokens: list[str] = []
        for key in keys:
            value = data_map.get(key)
            if value is None:
                value = context_map.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if not text:
                continue
            tokens.append(f"{key}={self._truncate_string(text, 96)}")

        return " ".join(tokens)

    # MARK: - Payload Sanitization

    def _truncate_message(self, message: str) -> str:
        """Clamp log message length to avoid oversized log entries."""
        return self._truncate_string(message, self._max_message_length)

    @staticmethod
    def _truncate_string(value: str, max_length: int) -> str:
        """Truncate string values while preserving a clear suffix marker."""
        if len(value) <= max_length:
            return value
        if max_length <= 3:
            return value[:max_length]
        return f"{value[: max_length - 3]}..."

    def _sanitize_mapping(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize dict payload for predictable, bounded log output."""
        visited: set[int] = set()
        items = list(data.items())
        limited_items = items[: self._max_collection_items]

        sanitized: dict[str, Any] = {}
        for key, value in limited_items:
            sanitized[str(key)] = self._sanitize_value(value, visited=visited, depth=0)

        remaining = len(items) - len(limited_items)
        if remaining > 0:
            sanitized["__truncated_items__"] = remaining

        return sanitized

    def _sanitize_value(self, value: Any, *, visited: set[int], depth: int) -> Any:
        """Recursively sanitize values while avoiding recursion and payload explosions."""
        if value is None or isinstance(value, (bool, int, float)):
            return value

        if isinstance(value, str):
            return self._truncate_string(value, self._max_string_length)

        if isinstance(value, bytes):
            return self._truncate_string(value.decode("utf-8", errors="replace"), 128)

        if depth >= 6:
            return "<max_depth_exceeded>"

        obj_id = id(value)
        if obj_id in visited:
            return "<recursive_reference>"

        if isinstance(value, dict):
            visited.add(obj_id)
            items = list(value.items())
            limited_items = items[: self._max_collection_items]
            nested: dict[str, Any] = {}
            for key, nested_value in limited_items:
                nested[str(key)] = self._sanitize_value(
                    nested_value,
                    visited=visited,
                    depth=depth + 1,
                )

            remaining = len(items) - len(limited_items)
            if remaining > 0:
                nested["__truncated_items__"] = remaining
            visited.remove(obj_id)
            return nested

        if isinstance(value, (list, tuple, set, frozenset)):
            visited.add(obj_id)
            sequence = list(value)
            limited_items = sequence[: self._max_collection_items]
            nested_list = [
                self._sanitize_value(item, visited=visited, depth=depth + 1)
                for item in limited_items
            ]
            remaining = len(sequence) - len(limited_items)
            if remaining > 0:
                nested_list.append(f"... (+{remaining} more items)")
            visited.remove(obj_id)
            return nested_list

        return self._truncate_string(str(value), self._max_string_length)
