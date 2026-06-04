"""Logging formatters for structured output.

This module provides various formatting strategies for log output,
including human-readable console formatting and structured JSON formatting.
"""

# pyright: strict
from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar, Final, TextIO

import orjson

from .config import (
    DEFAULT_HEADER_WIDTH,
    TIMESTAMP_FORMAT,
)

# MARK: - Timestamp Formatting


class TimestampFormatter:
    """Handles timestamp formatting for log entries."""

    @staticmethod
    def format_timestamp() -> str:
        """Generate ISO format timestamp for logging.

        Returns:
            ISO 8601 formatted timestamp string
        """
        return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)


# MARK: - Text Formatting


class TextFormatter:
    """Handles text formatting for console and display output."""

    @staticmethod
    def center_text(text: str, width: int = DEFAULT_HEADER_WIDTH, fill_char: str = " ") -> str:
        """Center text within a given width.

        Args:
            text: Text to center
            width: Total width for centering
            fill_char: Character to use for padding

        Returns:
            Centered text string
        """
        if len(text) >= width:
            return text
        padding = (width - len(text)) // 2
        return fill_char * padding + text + fill_char * (width - len(text) - padding)


# MARK: - Color Formatting


class ColorFormatter:
    """Handles ANSI color formatting for console output."""

    # MARK: - Basic Styles

    RESET: ClassVar[str] = "\033[0m"
    BOLD: ClassVar[str] = "\033[1m"
    DIM: ClassVar[str] = "\033[2m"
    UNDERLINE: ClassVar[str] = "\033[4m"

    # MARK: - Foreground Colors

    BLACK: ClassVar[str] = "\033[30m"
    RED: ClassVar[str] = "\033[31m"
    GREEN: ClassVar[str] = "\033[32m"
    YELLOW: ClassVar[str] = "\033[33m"
    BLUE: ClassVar[str] = "\033[34m"
    MAGENTA: ClassVar[str] = "\033[35m"
    CYAN: ClassVar[str] = "\033[36m"
    WHITE: ClassVar[str] = "\033[37m"

    # MARK: - Bright Foreground Colors

    BRIGHT_BLACK: ClassVar[str] = "\033[90m"
    BRIGHT_RED: ClassVar[str] = "\033[91m"
    BRIGHT_GREEN: ClassVar[str] = "\033[92m"
    BRIGHT_YELLOW: ClassVar[str] = "\033[93m"
    BRIGHT_BLUE: ClassVar[str] = "\033[94m"
    BRIGHT_MAGENTA: ClassVar[str] = "\033[95m"
    BRIGHT_CYAN: ClassVar[str] = "\033[96m"
    BRIGHT_WHITE: ClassVar[str] = "\033[97m"

    # MARK: - Background Colors

    BG_BLACK: ClassVar[str] = "\033[40m"
    BG_RED: ClassVar[str] = "\033[41m"
    BG_GREEN: ClassVar[str] = "\033[42m"
    BG_YELLOW: ClassVar[str] = "\033[43m"
    BG_BLUE: ClassVar[str] = "\033[44m"
    BG_MAGENTA: ClassVar[str] = "\033[45m"
    BG_CYAN: ClassVar[str] = "\033[46m"
    BG_WHITE: ClassVar[str] = "\033[47m"

    # MARK: - Methods

    @staticmethod
    def colorize_text(text: str, color: str) -> str:
        """Apply color formatting to text.

        Args:
            text: Text to colorize
            color: Color code from ColorFormatter class

        Returns:
            Colorized text string
        """
        return f"{color}{text}{ColorFormatter.RESET}"


# MARK: - Log Styles


class LogStyles:
    """Standardized log message styles using ColorFormatter."""

    # MARK: - Level Colors

    DEBUG: ClassVar[str] = ColorFormatter.BRIGHT_BLACK
    INFO: ClassVar[str] = ColorFormatter.WHITE
    WARNING: ClassVar[str] = ColorFormatter.BRIGHT_YELLOW
    ERROR: ClassVar[str] = ColorFormatter.BRIGHT_RED
    CRITICAL: ClassVar[str] = ColorFormatter.BRIGHT_WHITE + ColorFormatter.BG_RED

    # MARK: - Component Colors

    SYSTEM: ClassVar[str] = ColorFormatter.BRIGHT_CYAN
    AGENT: ClassVar[str] = ColorFormatter.BRIGHT_GREEN
    NODE: ClassVar[str] = ColorFormatter.BRIGHT_MAGENTA
    TASK: ClassVar[str] = ColorFormatter.BRIGHT_BLUE
    TOOL: ClassVar[str] = ColorFormatter.BRIGHT_YELLOW
    SESSION: ClassVar[str] = ColorFormatter.BRIGHT_WHITE

    # MARK: - Execution Styles

    EXECUTION_START: ClassVar[str] = ColorFormatter.BRIGHT_GREEN + ColorFormatter.BOLD
    EXECUTION_END: ClassVar[str] = ColorFormatter.BRIGHT_BLUE + ColorFormatter.BOLD
    EXECUTION_ERROR: ClassVar[str] = ColorFormatter.BRIGHT_RED + ColorFormatter.BOLD
    EXECUTION_HIGHLIGHT: ClassVar[str] = ColorFormatter.BRIGHT_MAGENTA + ColorFormatter.BOLD


# MARK: - Style Lookup

_LOG_STYLE_BY_NAME: Final[dict[str, str]] = {
    "DEBUG": LogStyles.DEBUG,
    "INFO": LogStyles.INFO,
    "WARNING": LogStyles.WARNING,
    "ERROR": LogStyles.ERROR,
    "CRITICAL": LogStyles.CRITICAL,
    "SYSTEM": LogStyles.SYSTEM,
    "AGENT": LogStyles.AGENT,
    "NODE": LogStyles.NODE,
    "TASK": LogStyles.TASK,
    "TOOL": LogStyles.TOOL,
    "SESSION": LogStyles.SESSION,
    "EXECUTION_START": LogStyles.EXECUTION_START,
    "EXECUTION_END": LogStyles.EXECUTION_END,
    "EXECUTION_ERROR": LogStyles.EXECUTION_ERROR,
    "EXECUTION_HIGHLIGHT": LogStyles.EXECUTION_HIGHLIGHT,
}


def resolve_log_style(name: str, default: str = ColorFormatter.WHITE) -> str:
    """Return a typed log style by name, falling back to ``default``."""
    return _LOG_STYLE_BY_NAME.get(name, default)


# MARK: - Human Readable Formatting


class HumanReadableFormatter:
    """Formats log messages for human-readable console output."""

    @staticmethod
    def format_readable_log_message(
        level: str, component: str, message: str, use_colors: bool = True
    ) -> str:
        """Format a message for human-readable console output with optional colors.

        Args:
            level: Log level
            component: Component name
            message: Log message
            use_colors: Whether to use colors (default True)

        Returns:
            Formatted readable message
        """
        timestamp = TimestampFormatter.format_timestamp()

        if use_colors:
            level_color = resolve_log_style(level)
            level_colored = ColorFormatter.colorize_text(f"[{level}]", level_color)

            component_color = resolve_log_style(component.upper())
            component_colored = ColorFormatter.colorize_text(f"[{component}]", component_color)

            return f"[{timestamp}] {level_colored} {component_colored} {message}"

        return f"[{timestamp}] [{level}] [{component}] {message}"

    @staticmethod
    def format_log_line(timestamp: str, level: str, component: str, message: str) -> str:
        """Format a log line with timestamp, level, and component.

        Args:
            timestamp: ISO format timestamp
            level: Log level
            component: Component name
            message: Log message

        Returns:
            Formatted log line with newline
        """
        return f"[{timestamp}] [{level}] [{component}] {message}\n"


# MARK: - JSON Formatting


class JSONFormatter:
    """Handles JSON formatting for structured log output."""

    @staticmethod
    def safe_json_dumps(data: object) -> str:
        """Safely serialize data to JSON string using orjson.

        Args:
            data: Data to serialize

        Returns:
            JSON string representation
        """
        return orjson.dumps(data, default=str).decode("utf-8")


# MARK: - Stream Writing


class StreamWriter:
    """Handles writing to output streams with error handling."""

    @staticmethod
    def write_to_stream(stream: TextIO, content: str) -> None:
        """Write content to a stream with error handling.

        Args:
            stream: Output stream (file or stdout/stderr)
            content: Content to write
        """
        try:
            _ = stream.write(content)
            stream.flush()
        except Exception as e:  # noqa: BLE001 - logging must not raise stream failures.
            import sys

            # Last-resort stderr fallback must stay ASCII-only.
            print(f"[MaivnLogger] Failed to write log: {e}", file=sys.stderr)


# MARK: - Exports

__all__ = [
    "TimestampFormatter",
    "TextFormatter",
    "ColorFormatter",
    "LogStyles",
    "resolve_log_style",
    "HumanReadableFormatter",
    "JSONFormatter",
    "StreamWriter",
]
