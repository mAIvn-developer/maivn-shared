# pyright: strict
"""Internal helpers for redacting sensitive values."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast

REDACTED = "[REDACTED]"

_MAX_REDACTION_DEPTH = 8

_SENSITIVE_KEY_MARKERS = frozenset(
    {
        "access_key",
        "access_token",
        "api_key",
        "apikey",
        "authorization",
        "bearer",
        "credential",
        "passphrase",
        "password",
        "passwd",
        "private_data",
        "private_key",
        "refresh_token",
        "secret",
        "service_key",
        "session_token",
        "token",
    }
)


def is_sensitive_key(key: str) -> bool:
    """Return True when a mapping key conventionally carries sensitive data."""
    normalized = key.lower().replace("-", "_")
    return any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS)


def redact_sensitive_data(value: object) -> object:
    """Recursively redact values whose keys indicate secrets or private data."""
    return _redact_value(value, depth=0)


def _redact_value(value: object, *, depth: int) -> object:
    if depth >= _MAX_REDACTION_DEPTH:
        return value

    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        return {
            key: REDACTED if is_sensitive_key(str(key)) else _redact_value(item, depth=depth + 1)
            for key, item in mapping.items()
        }

    if isinstance(value, list):
        sequence = cast(Iterable[object], value)
        return [_redact_value(item, depth=depth + 1) for item in sequence]

    if isinstance(value, tuple):
        sequence = cast(Iterable[object], value)
        return tuple(_redact_value(item, depth=depth + 1) for item in sequence)

    if isinstance(value, set | frozenset):
        return [_redact_value(item, depth=depth + 1) for item in cast(Iterable[object], value)]

    return value


__all__ = [
    "REDACTED",
    "is_sensitive_key",
    "redact_sensitive_data",
]
