# pyright: strict
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
from collections.abc import Callable, Iterable, Mapping
from typing import Protocol, cast, runtime_checkable

import orjson
from pydantic import JsonValue

from maivn_shared._redaction import redact_sensitive_data
from maivn_shared.domain.exceptions import MaivnError, is_retryable

# MARK: - Protocols


@runtime_checkable
class _JsonModel(Protocol):
    def model_dump(self, *, mode: str) -> object: ...


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
_PUBLIC_ERROR_MESSAGE = "An internal error occurred."


# MARK: - Core Functions


def to_jsonable(obj: object) -> JsonValue:
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


def dumps(obj: object, *, pretty: bool = False) -> str:
    """Serialize object to JSON string using orjson.

    Args:
        obj: Object to serialize
        pretty: If True, output indented JSON with sorted keys

    Returns:
        JSON string representation
    """
    options = _PRETTY_OPTIONS if pretty else _DEFAULT_OPTIONS
    return orjson.dumps(obj, default=_orjson_default, option=options).decode("utf-8")


def dumps_bytes(obj: object, *, pretty: bool = False) -> bytes:
    """Serialize object to JSON bytes using orjson.

    More efficient than dumps() when bytes output is acceptable.
    Avoids the UTF-8 decode overhead of dumps().

    Key order: when ``pretty=False`` (the default) keys are emitted in the
    object's insertion order and are NOT sorted; only ``pretty=True`` adds
    ``OPT_SORT_KEYS``. Callers that hash this output (e.g. content hashing in
    ``tool_hash_service``) must therefore pre-normalize key order themselves, or
    two dicts with equal content built in different orders will hash differently.

    Args:
        obj: Object to serialize
        pretty: If True, output indented JSON with sorted keys

    Returns:
        JSON bytes representation
    """
    options = _PRETTY_OPTIONS if pretty else _DEFAULT_OPTIONS
    return orjson.dumps(obj, default=_orjson_default, option=options)


def loads(data: str | bytes) -> JsonValue:
    """Deserialize JSON string or bytes to Python object.

    Args:
        data: JSON string or bytes

    Returns:
        Deserialized Python object
    """
    return cast(JsonValue, orjson.loads(data))


# MARK: - Error Serialization


def serialize_error(error: Exception) -> dict[str, object]:
    """Serialize an exception to a JSON-friendly internal dictionary.

    This helper includes raw exception text and args. Use
    ``serialize_public_error`` for public API responses or client-visible
    errors.

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


def serialize_public_error(
    error: Exception,
    *,
    message: str = _PUBLIC_ERROR_MESSAGE,
) -> dict[str, object]:
    """Serialize an exception without raw text, args, context, or causes."""
    if isinstance(error, MaivnError):
        return error.to_public_dict(message=message)

    return {
        "error_type": type(error).__name__,
        "error_code": type(error).__name__,
        "message": message,
        "retryable": is_retryable(error),
    }


def safe_public_jsonable(obj: object) -> JsonValue:
    """Return a JSON-compatible representation with sensitive keys redacted."""
    return cast(JsonValue, redact_sensitive_data(to_jsonable(obj)))


# MARK: - Internal Helpers


def _dispatch_leaf(obj: object, recurse: Callable[[object], object]) -> object:
    """Shared custom-type dispatch for the two serialization entry points.

    Handles the type ladder both ``_orjson_default`` and ``_serialize_object``
    share: Pydantic model, dataclass, set/frozenset, bytes, ``__dict__`` object,
    str fallback. The ``recurse`` callback decides how nested values are handled:

    - ``_orjson_default`` passes the identity callback and relies on orjson to
      re-serialize set elements and ``__dict__`` values natively.
    - ``_serialize_object`` passes itself, fully serializing nested values.

    Both paths sort set output by ``_sort_key`` over the (possibly recursed)
    element, preserving the original per-entry-point ordering byte-for-byte.
    """
    # Pydantic v2 models
    if isinstance(obj, _JsonModel):
        return obj.model_dump(mode="json")

    # Dataclasses
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)

    # Sets/frozensets
    if isinstance(obj, set | frozenset):
        return sorted(
            [recurse(item) for item in cast(Iterable[object], obj)],
            key=_sort_key,
        )

    # Bytes
    if isinstance(obj, bytes):
        return _decode_bytes(obj)

    # Objects with __dict__
    attributes = _object_dict(obj)
    if attributes is not None:
        return recurse(attributes)

    # Fallback to string
    return _safe_str(obj)


def _orjson_default(obj: object) -> object:
    """orjson default handler for custom types.

    orjson natively serializes None/bool/int/float/str/dict/list, so this is only
    invoked for the custom types in ``_dispatch_leaf``. Nested values are returned
    unchanged for orjson to recurse over.
    """
    return _dispatch_leaf(obj, lambda value: value)


def _serialize_object(obj: object) -> JsonValue:
    """Internal recursive serialization logic."""
    if obj is None:
        return None

    if isinstance(obj, str | int | float | bool):
        return obj

    if isinstance(obj, bytes):
        return _decode_bytes(obj)

    if isinstance(obj, dict):
        mapping = cast(Mapping[object, object], obj)
        return {_serialize_key(k): _serialize_object(v) for k, v in mapping.items()}

    if isinstance(obj, list | tuple):
        return [_serialize_object(item) for item in cast(Iterable[object], obj)]

    return cast(JsonValue, _dispatch_leaf(obj, _serialize_object))


def _serialize_key(key: object) -> str:
    """Convert dictionary key to string."""
    return key if isinstance(key, str) else str(key)


def _sort_key(item: object) -> tuple[int, str]:
    """Generate sort key for mixed-type lists.

    Numbers are keyed by ``str(item)``, so a numeric set sorts lexicographically
    (``{2, 10, 1}`` -> ``[1, 10, 2]``), not by numeric value. This is intentional:
    the only goal here is a *deterministic* ordering for set serialization.
    Switching to numeric ordering would change existing serialized output and so
    shift any hashes or snapshots computed over set-containing payloads.
    """
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


def _safe_str(obj: object) -> str:
    """Convert object to string with fallback."""
    try:
        return str(obj)
    except Exception:  # noqa: BLE001 - best-effort fallback; value degrades to a placeholder.
        return f"<{type(obj).__name__}>"


def _object_dict(obj: object) -> Mapping[str, object] | None:
    """Return object attributes for instances that expose __dict__."""
    try:
        return cast(Mapping[str, object], vars(obj))
    except TypeError:
        return None


# MARK: - Exports

__all__ = [
    "dumps",
    "dumps_bytes",
    "loads",
    "safe_public_jsonable",
    "serialize_error",
    "serialize_public_error",
    "to_jsonable",
]
