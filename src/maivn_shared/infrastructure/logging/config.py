"""Logging configuration constants and settings.

This module centralizes all logging-related configuration values,
formatting constants, and system settings for the Maivn logging infrastructure.
"""

# pyright: strict
from __future__ import annotations

import os
from typing import Literal

# MARK: Type Definitions

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF"]

# MARK: - Constants

_VALID_LOG_LEVELS: frozenset[LogLevel] = frozenset(
    {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF"}
)

# MARK: - Helper Functions


def _get_log_level_from_env(env_var: str, default: LogLevel) -> LogLevel:
    """Get and validate a log level from an environment variable.

    Args:
        env_var: Name of the environment variable
        default: Default log level if env var is not set or invalid

    Returns:
        Validated log level
    """
    value = os.getenv(env_var, "").upper()
    # Return the matching LogLevel member so the validity invariant is explicit
    # (and the narrowed type is sourced from _VALID_LOG_LEVELS, not str luck).
    for valid_level in _VALID_LOG_LEVELS:
        if value == valid_level:
            return valid_level
    return default


def _get_int_from_env(env_var: str, default: int, *, minimum: int | None = None) -> int:
    """Read an integer from environment with optional lower bound validation."""
    raw_value = os.getenv(env_var)
    if raw_value is None:
        return default

    try:
        parsed = int(raw_value)
    except ValueError:
        return default

    if minimum is not None and parsed < minimum:
        return default

    return parsed


# MARK: Logging Configuration Constants

# MARK: - Console Settings

DEFAULT_CONSOLE_LEVEL: LogLevel = _get_log_level_from_env("MAIVN_LOG_LEVEL", "OFF")
DEFAULT_FILE_LEVEL: LogLevel = _get_log_level_from_env("MAIVN_FILE_LOG_LEVEL", "INFO")
DEFAULT_USE_COLORS: bool = True
DEFAULT_HUMAN_READABLE_CONSOLE: bool = True

# MARK: - Log Level Priorities

LOG_LEVEL_PRIORITY: dict[LogLevel, int] = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "ERROR": 3,
    "CRITICAL": 4,
    "OFF": 99,
}

# MARK: Output Format Configuration

TIMESTAMP_FORMAT: str = "%Y-%m-%dT%H:%M:%S.%fZ"
DEFAULT_HEADER_WIDTH: int = 80

# MARK: System Events

SYSTEM_EVENTS: frozenset[str] = frozenset(
    {
        "STARTUP",
        "SHUTDOWN",
        "CONFIGURATION_LOADED",
        "DEPENDENCY_RESOLVED",
        "execution_startup",
    }
)

# MARK: Async Configuration

DEFAULT_QUEUE_SIZE: int = _get_int_from_env("MAIVN_LOG_QUEUE_SIZE", 1000, minimum=1)

# MARK: Log Bloat Controls

DEFAULT_MAX_MESSAGE_LENGTH: int = _get_int_from_env(
    "MAIVN_LOG_MAX_MESSAGE_LENGTH",
    400,
    minimum=64,
)
DEFAULT_MAX_STRING_LENGTH: int = _get_int_from_env(
    "MAIVN_LOG_MAX_STRING_LENGTH",
    512,
    minimum=64,
)
DEFAULT_MAX_COLLECTION_ITEMS: int = _get_int_from_env(
    "MAIVN_LOG_MAX_COLLECTION_ITEMS",
    25,
    minimum=1,
)

# MARK: Module Exports

__all__ = [
    # Types
    "LogLevel",
    # Console settings
    "DEFAULT_CONSOLE_LEVEL",
    "DEFAULT_FILE_LEVEL",
    "DEFAULT_USE_COLORS",
    "DEFAULT_HUMAN_READABLE_CONSOLE",
    # Log levels
    "LOG_LEVEL_PRIORITY",
    # Format settings
    "TIMESTAMP_FORMAT",
    "DEFAULT_HEADER_WIDTH",
    # System events
    "SYSTEM_EVENTS",
    # Async settings
    "DEFAULT_QUEUE_SIZE",
    # Bloat controls
    "DEFAULT_MAX_MESSAGE_LENGTH",
    "DEFAULT_MAX_STRING_LENGTH",
    "DEFAULT_MAX_COLLECTION_ITEMS",
]
