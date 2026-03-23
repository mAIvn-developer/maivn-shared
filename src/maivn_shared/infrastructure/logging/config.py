"""Logging configuration constants and settings.

This module centralizes all logging-related configuration values,
formatting constants, and system settings for the Maivn logging infrastructure.
"""

from __future__ import annotations

import os
from typing import Literal

# MARK: Type Definitions

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF"]

# MARK: - Constants

_VALID_LOG_LEVELS: frozenset[str] = frozenset(
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
    if value in _VALID_LOG_LEVELS:
        return value  # type: ignore[return-value]
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

LOG_LEVEL_PRIORITY: dict[str, int] = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "ERROR": 3,
    "CRITICAL": 4,
    "OFF": 99,
}

# MARK: Component-Specific Log Levels

COMPONENT_LOG_LEVELS: dict[str, LogLevel] = {
    "VALIDATION": _get_log_level_from_env("MAIVN_LOG_LEVEL_VALIDATION", "WARNING"),
    "STREAM": _get_log_level_from_env("MAIVN_LOG_LEVEL_STREAM", "INFO"),
    "SERVER_RECEIVED": _get_log_level_from_env("MAIVN_LOG_LEVEL_SERVER_RECEIVED", "DEBUG"),
    "UUID_TRACKER": _get_log_level_from_env("MAIVN_LOG_LEVEL_UUID_TRACKER", "DEBUG"),
}

# MARK: Output Format Configuration

TIMESTAMP_FORMAT: str = "%Y-%m-%dT%H:%M:%S.%fZ"
DEFAULT_HEADER_WIDTH: int = 80
DEFAULT_BORDER_CHAR: str = "="

# MARK: Component Categories

COMPONENT_CATEGORIES: dict[str, str] = {
    "SYSTEM": "System Operations",
    "AGENT": "Agent Operations",
    "NODE": "Node Execution",
    "TASK": "Task Processing",
    "TOOL": "Tool Execution",
    "SESSION": "Session Management",
    "ORCHESTRATION": "Workflow Orchestration",
    "EVENT_STREAM": "Event Streaming",
    "TOKEN_USAGE": "Token Usage Tracking",
    "TIMING": "Performance Timing",
    "USER_INPUT": "User Input Handling",
    "SCHEDULER": "Job Scheduling",
    "TOOL_CALL": "Tool Invocation",
    "TASK_PLANNING": "Task Planning",
    "TASK_VALIDATION": "Task Validation",
    "TASK_EXECUTION": "Task Execution",
}

# MARK: Event Types

EXECUTION_EVENTS: dict[str, str] = {
    "START": "Execution Started",
    "END": "Execution Completed",
    "ERROR": "Execution Failed",
    "INVOCATION_START": "Agent Invocation Started",
    "INVOCATION_END": "Agent Invocation Completed",
    "NODE_START": "Node Execution Started",
    "NODE_END": "Node Execution Completed",
    "SESSION_START": "Session Started",
    "SESSION_END": "Session Ended",
    "ORCHESTRATION_START": "Orchestration Started",
    "ORCHESTRATION_END": "Orchestration Completed",
    "ORCHESTRATION_FAILED": "Orchestration Failed",
}

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

# MARK: File Logging Configuration

DEFAULT_LOG_BUFFER_SIZE: int = 8192
DEFAULT_LOG_FILE_MODE: str = "a"
DEFAULT_LOG_FILE_ENCODING: str = "utf-8"

# MARK: Async Configuration

DEFAULT_THREAD_POOL_SIZE: int = 4
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
    "COMPONENT_LOG_LEVELS",
    # Format settings
    "TIMESTAMP_FORMAT",
    "DEFAULT_HEADER_WIDTH",
    "DEFAULT_BORDER_CHAR",
    # Categories and events
    "COMPONENT_CATEGORIES",
    "EXECUTION_EVENTS",
    "SYSTEM_EVENTS",
    # File logging
    "DEFAULT_LOG_BUFFER_SIZE",
    "DEFAULT_LOG_FILE_MODE",
    "DEFAULT_LOG_FILE_ENCODING",
    # Async settings
    "DEFAULT_THREAD_POOL_SIZE",
    "DEFAULT_QUEUE_SIZE",
    # Bloat controls
    "DEFAULT_MAX_MESSAGE_LENGTH",
    "DEFAULT_MAX_STRING_LENGTH",
    "DEFAULT_MAX_COLLECTION_ITEMS",
]
