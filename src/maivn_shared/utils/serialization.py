"""High-performance JSON serialization utilities using orjson.

This module provides unified JSON serialization functionality shared across
maivn packages. Uses orjson for ~10x faster serialization than stdlib json.

Features:
- Automatic Pydantic model serialization
- Dataclass support
- Set/tuple to list conversion
- Graceful fallbacks for complex objects
- Error serialization helpers
"""

from __future__ import annotations

import dataclasses
from typing import Any

import orjson

# MARK: - Constants

# Default orjson options for consistent output
_DEFAULT_OPTIONS = orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_UTC_Z | orjson.OPT_PASSTHROUGH_DATACLASS

_PRETTY_OPTIONS = _DEFAULT_OPTIONS | orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS

# Type ordering for deterministic sorting
_TYPE_ORDER_NONE = 0
_TYPE_ORDER_BOOL = 1
_TYPE_ORDER_NUMBER = 2
_TYPE_ORDER_STRING = 3
_TYPE_ORDER_OTHER = 4


# MARK: - Core Functions


def to_jsonable(obj: Any) -> Any:
    """Convert an object to JSON-serializable format.

    Recursively processes objects to ensure JSON compatibility:
    - Pydantic models: Uses model_dump(mode='json')
    - Dataclasses: Uses dataclasses.asdict()
    - Sets/tuples: Converted to lists
    - Objects with __dict__: Recursively serialized
    - Everything else: String conversion fallback

    Args:
        obj: Object to serialize

    Returns:
        JSON-serializable representation of the object
    """
    return _serialize_object(obj)


def dumps(obj: Any, *, pretty: bool = False) -> str:
    """Serialize object to JSON string using orjson.

    Args:
        obj: Object to serialize
        pretty: If True, output indented JSON with sorted keys

    Returns:
        JSON string representation
    """
    options = _PRETTY_OPTIONS if pretty else _DEFAULT_OPTIONS
    return orjson.dumps(obj, default=_orjson_default, option=options).decode("utf-8")


def dumps_bytes(obj: Any, *, pretty: bool = False) -> bytes:
    """Serialize object to JSON bytes using orjson.

    More efficient than dumps() when bytes output is acceptable.
    Avoids the UTF-8 decode overhead of dumps().

    Args:
        obj: Object to serialize
        pretty: If True, output indented JSON with sorted keys

    Returns:
        JSON bytes representation
    """
    options = _PRETTY_OPTIONS if pretty else _DEFAULT_OPTIONS
    return orjson.dumps(obj, default=_orjson_default, option=options)


def loads(data: str | bytes) -> Any:
    """Deserialize JSON string or bytes to Python object.

    Args:
        data: JSON string or bytes

    Returns:
        Deserialized Python object
    """
    return orjson.loads(data)


# MARK: - Error Serialization


def serialize_error(error: Exception) -> dict[str, Any]:
    """Serialize an exception to a JSON-friendly dictionary.

    Args:
        error: Exception to serialize

    Returns:
        Dictionary containing error_type, error_message, and error_args
    """
    return {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_args": list(error.args) if error.args else [],
    }


def serialize_with_metadata(obj: Any, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Serialize an object with additional metadata.

    Args:
        obj: Object to serialize
        metadata: Additional metadata to include

    Returns:
        Dictionary with data, type, and optional metadata
    """
    result: dict[str, Any] = {
        "data": to_jsonable(obj),
        "type": type(obj).__name__,
    }

    if metadata:
        result["metadata"] = to_jsonable(metadata)

    return result


# MARK: - Internal Helpers


def _orjson_default(obj: Any) -> Any:
    """orjson default handler for custom types."""
    # Pydantic v2 models
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")

    # Dataclasses
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)

    # Sets/frozensets
    if isinstance(obj, set | frozenset):
        return sorted(obj, key=_sort_key)

    # Bytes
    if isinstance(obj, bytes):
        return _decode_bytes(obj)

    # Objects with __dict__
    if hasattr(obj, "__dict__"):
        return obj.__dict__

    # Fallback to string
    return _safe_str(obj)


def _serialize_object(obj: Any) -> Any:
    """Internal recursive serialization logic."""
    if obj is None:
        return None

    if isinstance(obj, str | int | float | bool):
        return obj

    if isinstance(obj, bytes):
        return _decode_bytes(obj)

    if isinstance(obj, dict):
        return {_serialize_key(k): _serialize_object(v) for k, v in obj.items()}

    if isinstance(obj, list | tuple):
        return [_serialize_object(item) for item in obj]

    if isinstance(obj, set | frozenset):
        return sorted([_serialize_object(item) for item in obj], key=_sort_key)

    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")

    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)

    if hasattr(obj, "__dict__"):
        return _serialize_object(obj.__dict__)

    return _safe_str(obj)


def _serialize_key(key: Any) -> str:
    """Convert dictionary key to string."""
    return key if isinstance(key, str) else str(key)


def _sort_key(item: Any) -> tuple[int, str]:
    """Generate sort key for mixed-type lists."""
    if item is None:
        return (_TYPE_ORDER_NONE, "")
    if isinstance(item, bool):
        return (_TYPE_ORDER_BOOL, str(item))
    if isinstance(item, int | float):
        return (_TYPE_ORDER_NUMBER, str(item))
    if isinstance(item, str):
        return (_TYPE_ORDER_STRING, item)
    return (_TYPE_ORDER_OTHER, str(item))


def _decode_bytes(data: bytes) -> str:
    """Decode bytes to string with fallback."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return f"<bytes: {len(data)} bytes>"


def _safe_str(obj: Any) -> str:
    """Convert object to string with fallback."""
    try:
        return str(obj)
    except Exception:
        return f"<{type(obj).__name__}>"


# MARK: - Exports

__all__ = [
    "dumps",
    "dumps_bytes",
    "loads",
    "serialize_error",
    "serialize_with_metadata",
    "to_jsonable",
]
