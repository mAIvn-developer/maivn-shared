"""Logging formatters for structured output.

This module provides various formatting strategies for log output,
including human-readable console formatting and structured JSON formatting.
"""

# MARK: - Imports

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TextIO

import orjson

from .config import (
    DEFAULT_BORDER_CHAR,
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

    @staticmethod
    def create_section_header(
        title: str, width: int = DEFAULT_HEADER_WIDTH, border_char: str = DEFAULT_BORDER_CHAR
    ) -> str:
        """Create a formatted section header.

        Args:
            title: Header title text
            width: Total width of the header
            border_char: Character to use for borders

        Returns:
            Formatted header string
        """
        if len(title) >= width - 4:
            return border_char * width

        padding = (width - len(title) - 2) // 2
        return (
            border_char * padding
            + " "
            + title
            + " "
            + border_char * (width - len(title) - padding - 2)
        )


# MARK: - Color Formatting


class ColorFormatter:
    """Handles ANSI color formatting for console output."""

    # MARK: - Basic Styles

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # MARK: - Foreground Colors

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # MARK: - Bright Foreground Colors

    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # MARK: - Background Colors

    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

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

    DEBUG = ColorFormatter.BRIGHT_BLACK
    INFO = ColorFormatter.WHITE
    WARNING = ColorFormatter.BRIGHT_YELLOW
    ERROR = ColorFormatter.BRIGHT_RED
    CRITICAL = ColorFormatter.BRIGHT_WHITE + ColorFormatter.BG_RED

    # MARK: - Component Colors

    SYSTEM = ColorFormatter.BRIGHT_CYAN
    AGENT = ColorFormatter.BRIGHT_GREEN
    NODE = ColorFormatter.BRIGHT_MAGENTA
    TASK = ColorFormatter.BRIGHT_BLUE
    TOOL = ColorFormatter.BRIGHT_YELLOW
    SESSION = ColorFormatter.BRIGHT_WHITE

    # MARK: - Execution Styles

    EXECUTION_START = ColorFormatter.BRIGHT_GREEN + ColorFormatter.BOLD
    EXECUTION_END = ColorFormatter.BRIGHT_BLUE + ColorFormatter.BOLD
    EXECUTION_ERROR = ColorFormatter.BRIGHT_RED + ColorFormatter.BOLD
    EXECUTION_HIGHLIGHT = ColorFormatter.BRIGHT_MAGENTA + ColorFormatter.BOLD


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
            level_color = getattr(LogStyles, level, ColorFormatter.WHITE)
            level_colored = ColorFormatter.colorize_text(f"[{level}]", level_color)

            component_color = getattr(LogStyles, component.upper(), ColorFormatter.WHITE)
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
    def safe_json_dumps(data: Any) -> str:
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
            stream.write(content)
            stream.flush()
        except Exception as e:
            import sys

            print(f"[MaivnLogger] Failed to write log: {e}", file=sys.stderr)

    @staticmethod
    def write_json_entry(stream: TextIO, entry: dict[str, Any]) -> None:
        """Write a JSON log entry to a stream.

        Args:
            stream: Output stream
            entry: Log entry data
        """
        json_str = JSONFormatter.safe_json_dumps(entry)
        StreamWriter.write_to_stream(stream, f"{json_str}\n")


# MARK: - Exports

__all__ = [
    "TimestampFormatter",
    "TextFormatter",
    "ColorFormatter",
    "LogStyles",
    "HumanReadableFormatter",
    "JSONFormatter",
    "StreamWriter",
]
