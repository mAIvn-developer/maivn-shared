"""Maivn platform logger - factory and global instance management.

This module provides:
- get_logger(): Get the global MaivnLogger instance
- get_optional_logger(): Get logger or NullLogger fallback
"""

from __future__ import annotations

from pathlib import Path

from .maivn_logger import MaivnLogger
from .null_logger import NullLogger

# MARK: Global Instance Management

_logger_instance: MaivnLogger | None = None


def get_logger(log_file_path: Path | str | None = None) -> MaivnLogger:
    """Get the global Maivn logger instance.

    Args:
        log_file_path: Full path to log file (only used on first initialization).
            If None, only console logging is enabled.

    Returns:
        MaivnLogger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = MaivnLogger(log_file_path=log_file_path)
    return _logger_instance


def get_optional_logger() -> MaivnLogger | NullLogger:
    """Get Maivn logger if available, NullLogger otherwise.

    This is a safe helper for optional logging that doesn't raise
    exceptions if the logger is unavailable. Returns a NullLogger
    that implements the same interface but does nothing.

    Returns:
        MaivnLogger instance or NullLogger
    """
    try:
        return get_logger()
    except Exception:  # pragma: no cover
        return NullLogger()  # type: ignore


__all__ = ["MaivnLogger", "NullLogger", "get_logger", "get_optional_logger"]
