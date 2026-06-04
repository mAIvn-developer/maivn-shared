"""Maivn platform logger - factory and global instance management.

This module provides:
- get_logger(): Get the global MaivnLogger instance
- get_optional_logger(): Get logger or NullLogger fallback
"""

# pyright: strict
from __future__ import annotations

import threading
from pathlib import Path

from .maivn_logger import MaivnLogger
from .null_logger import NullLogger
from .protocols import LoggerProtocol

# MARK: Global Instance Management

_logger_instance: MaivnLogger | None = None
_logger_lock: threading.Lock = threading.Lock()


def get_logger(log_file_path: Path | str | None = None) -> MaivnLogger:
    """Get the global Maivn logger instance.

    Thread-safe: the lazy first-call initialization is guarded by a lock with
    double-checked locking so concurrent callers share a single logger (and a
    single background writer thread) instead of racing to construct duplicates.

    Args:
        log_file_path: Full path to log file (only used on first initialization).
            If None, only console logging is enabled.

    Returns:
        MaivnLogger instance
    """
    global _logger_instance
    if _logger_instance is None:
        with _logger_lock:
            if _logger_instance is None:
                _logger_instance = MaivnLogger(log_file_path=log_file_path)
    return _logger_instance


def get_optional_logger() -> LoggerProtocol:
    """Get Maivn logger if available, NullLogger otherwise.

    This is a safe helper for optional logging that doesn't raise
    exceptions if the logger is unavailable. Returns a NullLogger
    that implements the same interface but does nothing.

    Returns:
        MaivnLogger instance or NullLogger
    """
    try:
        return get_logger()
    except Exception:  # noqa: BLE001 - optional logging must never raise into callers.
        return NullLogger()


__all__ = ["MaivnLogger", "NullLogger", "get_logger", "get_optional_logger"]
