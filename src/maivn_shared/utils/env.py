from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, Protocol

# MARK: - Protocols


class _WarnLogger(Protocol):
    def warning(self, message: str, /, *args: Any, **kwargs: Any) -> None: ...


# MARK: - Types


EnvMapping = Mapping[str, str]

_FALSY_VALUES = frozenset({"0", "false", "False", "FALSE", "no", "No", "NO", ""})


# MARK: - Environment Resolution


def resolve_env(source: EnvMapping | None) -> EnvMapping:
    """Return the provided mapping or fall back to os.environ."""
    return source if source is not None else os.environ


# MARK: - Environment Getters


def get_env(name: str, default: str, env: EnvMapping) -> str:
    """Get a string environment variable with a default."""
    value = env.get(name)
    return value if value is not None else default


def get_env_bool(name: str, default: bool, env: EnvMapping) -> bool:
    """Parse a boolean environment variable."""
    raw = env.get(name)
    if raw is None:
        return default
    return raw not in _FALSY_VALUES


def get_env_float(
    name: str,
    default: float,
    env: EnvMapping,
    *,
    logger: _WarnLogger | None = None,
) -> float:
    """Parse a float environment variable."""
    raw = env.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        if logger is not None:
            logger.warning("Invalid float for %s=%s. Using default %s.", name, raw, default)
        return default


def get_env_int(
    name: str,
    default: int,
    env: EnvMapping,
    *,
    logger: _WarnLogger | None = None,
) -> int:
    """Parse an integer environment variable."""
    raw = env.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        if logger is not None:
            logger.warning("Invalid int for %s=%s. Using default %s.", name, raw, default)
        return default


# MARK: - Dictionary Utilities


def remove_none_values(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively remove None values from a dictionary."""
    cleaned: dict[str, Any] = {}

    for key, value in d.items():
        if isinstance(value, dict):
            nested = remove_none_values(value)
            if nested:
                cleaned[key] = nested
        elif value is not None:
            cleaned[key] = value

    return cleaned
