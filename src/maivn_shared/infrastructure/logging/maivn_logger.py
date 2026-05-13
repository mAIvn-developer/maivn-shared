"""Maivn platform logger: initialization, write path, and payload sanitization.

The public surface (level methods, execution-lifecycle methods, metrics
emission) lives in sibling mixins to keep this file focused on the
infrastructure shared by all of them: configuring the writer, building
log entries, formatting console/file output, and bounding payload size.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._logger_execution import MaivnLoggerExecutionMixin
from ._logger_levels import MaivnLoggerLevelsMixin
from ._logger_metrics import MaivnLoggerMetricsMixin
from .config import (
    DEFAULT_CONSOLE_LEVEL,
    DEFAULT_FILE_LEVEL,
    DEFAULT_HUMAN_READABLE_CONSOLE,
    DEFAULT_MAX_COLLECTION_ITEMS,
    DEFAULT_MAX_MESSAGE_LENGTH,
    DEFAULT_MAX_STRING_LENGTH,
    DEFAULT_USE_COLORS,
    LOG_LEVEL_PRIORITY,
    LogLevel,
)
from .context import ContextManager
from .formatters import (
    HumanReadableFormatter,
    JSONFormatter,
    TimestampFormatter,
)
from .writers import LogWriter

# MARK: MaivnLogger


class MaivnLogger(
    MaivnLoggerLevelsMixin,
    MaivnLoggerExecutionMixin,
    MaivnLoggerMetricsMixin,
):
    """Main Maivn platform logger with full functionality.

    Composed from three mixins (levels, execution-lifecycle, metrics) over a
    core that owns initialization, the structured-write path, and payload
    sanitization. See :class:`MaivnLoggerLevelsMixin`,
    :class:`MaivnLoggerExecutionMixin`, and :class:`MaivnLoggerMetricsMixin`
    for the per-cluster surface.
    """

    # MARK: - Initialization

    def __init__(
        self,
        log_file_path: Path | str | None = None,
        console_level: LogLevel = DEFAULT_CONSOLE_LEVEL,
        file_level: LogLevel = DEFAULT_FILE_LEVEL,
        use_colors: bool = DEFAULT_USE_COLORS,
        human_readable_console: bool = DEFAULT_HUMAN_READABLE_CONSOLE,
    ) -> None:
        """Initialize the logger.

        Args:
            log_file_path: Full path to log file (``None`` disables file logging).
            console_level: Minimum level for console output (default: ``OFF``).
            file_level: Minimum level for file output (default: ``INFO``).
            use_colors: Colorize console output when True.
            human_readable_console: Use the human-readable console format
                when True; emit raw JSON when False.
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
        """Build the underlying file/console writer."""
        log_file = Path(log_file_path) if log_file_path else None
        if log_file:
            log_file.parent.mkdir(exist_ok=True, parents=True)
        return LogWriter(log_file)

    def _log_startup_once(self) -> None:
        """Emit the startup banner exactly once per logger instance."""
        if self._initialized and not self._startup_logged:
            self._startup_logged = True
            self.log_system_startup()

    # MARK: - Context Management

    def set_context(self, **kwargs: Any) -> None:
        """Set context values that attach to all subsequent log entries."""
        self._context_manager.set(**kwargs)

    def clear_context(self, *keys: str) -> None:
        """Clear specific context keys, or all of them if no keys are passed."""
        self._context_manager.clear(*keys)

    def get_context(self) -> dict[str, Any]:
        """Return a copy of the current execution context's logging state."""
        return self._context_manager.get_context()

    # MARK: - Write Path

    def _should_log_to_console(self, level: LogLevel) -> bool:
        """Return True if ``level`` clears the configured console threshold."""
        return self._level_priority[level] >= self._level_priority[self._console_level]

    def _should_log_to_file(self, level: LogLevel) -> bool:
        """Return True if ``level`` clears the configured file threshold."""
        return self._level_priority[level] >= self._level_priority[self._file_level]

    def _log_at_level(
        self, level: LogLevel, message: str, *args: Any, component: str, **metadata: Any
    ) -> None:
        """Format ``message`` against ``args`` (printf-style) and dispatch via ``log_custom``."""
        formatted_message = message % args if args else message
        self.log_custom(level=level, component=component, message=formatted_message, **metadata)

    def _write_structured_log(
        self,
        level: LogLevel,
        component: str,
        event: str,
        data: dict[str, Any],
    ) -> None:
        """Build, sanitize, and emit a structured log entry to console + file."""
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
        """Assemble the structured entry dict with timestamp, level, component, event, and data."""
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
        """Render a log entry for the console (human-readable or JSON)."""
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
        """Render a log entry for the file (with appended correlation tokens)."""
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
        """Collect compact correlation fields (session_id, thread_id, …) for file logs."""
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
        """Clamp a log message to ``_max_message_length`` (suffix-marked)."""
        return self._truncate_string(message, self._max_message_length)

    @staticmethod
    def _truncate_string(value: str, max_length: int) -> str:
        """Truncate ``value`` to ``max_length``, preserving a clear ``...`` suffix marker."""
        if len(value) <= max_length:
            return value
        if max_length <= 3:
            return value[:max_length]
        return f"{value[: max_length - 3]}..."

    def _sanitize_mapping(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize a top-level dict payload to bounded depth/breadth/length."""
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
        """Recursively bound payload values; protect against cycles and depth explosions."""
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


__all__ = ["MaivnLogger"]
