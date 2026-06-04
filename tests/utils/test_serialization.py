# pyright: strict
from __future__ import annotations

import dataclasses
from typing import final, override

from pydantic import BaseModel

from maivn_shared.utils.redaction import REDACTED, redact_sensitive_data
from maivn_shared.utils.serialization import (
    dumps,
    dumps_bytes,
    loads,
    safe_public_jsonable,
    serialize_error,
    serialize_public_error,
    to_jsonable,
)

# MARK: Fixtures


class _Model(BaseModel):
    a: int = 1
    b: str = "x"


@dataclasses.dataclass
class _Point:
    x: int
    y: int


# MARK: dumps / dumps_bytes


def test_dumps_and_dumps_bytes_agree_on_simple_object() -> None:
    obj = {"k": [1, 2, 3], "n": None, "b": True}
    assert dumps(obj).encode("utf-8") == dumps_bytes(obj)


def test_dumps_bytes_preserves_insertion_order_when_not_pretty() -> None:
    # shared-utils-4: non-pretty output is NOT key-sorted; insertion order is kept.
    obj = {"z": 1, "a": 2, "m": 3}
    assert dumps_bytes(obj) == b'{"z":1,"a":2,"m":3}'


def test_dumps_pretty_sorts_keys() -> None:
    obj = {"z": 1, "a": 2}
    out = dumps(obj, pretty=True)
    assert out.index('"a"') < out.index('"z"')


def test_dumps_serializes_pydantic_model() -> None:
    assert loads(dumps(_Model())) == {"a": 1, "b": "x"}


def test_dumps_serializes_dataclass() -> None:
    assert loads(dumps(_Point(1, 2))) == {"x": 1, "y": 2}


def test_dumps_serializes_set_deterministically() -> None:
    # _orjson_default sorts set elements by _sort_key (lexicographic for numbers).
    assert loads(dumps({2, 10, 1})) == [1, 10, 2]


def test_dumps_decodes_bytes() -> None:
    assert loads(dumps({"data": b"hi"})) == {"data": "hi"}


def test_dumps_falls_back_to_str_for_unknown_object() -> None:
    @final
    class _Opaque:
        __slots__: tuple[str, ...] = ()

        @override
        def __str__(self) -> str:
            return "opaque"

    assert loads(dumps(_Opaque())) == "opaque"


# MARK: to_jsonable


def test_to_jsonable_recurses_through_nested_containers() -> None:
    obj = {"items": [{1, 2}, _Point(3, 4)], "raw": b"bytes"}
    assert to_jsonable(obj) == {
        "items": [[1, 2], {"x": 3, "y": 4}],
        "raw": "bytes",
    }


def test_to_jsonable_sorts_heterogeneous_set_lexicographically() -> None:
    # shared-utils-8: numbers sort by str() form within their bucket.
    assert to_jsonable({2, 10, 1}) == [1, 10, 2]


def test_to_jsonable_orders_mixed_type_set_by_type_bucket() -> None:
    result = to_jsonable({None, True, 5, "z"})
    # None bucket, then bool, then number, then string.
    assert result == [None, True, 5, "z"]


# MARK: serialize_error


def test_serialize_error_captures_type_message_and_args() -> None:
    err = ValueError("boom", 42)
    assert serialize_error(err) == {
        "error_type": "ValueError",
        "error_message": "('boom', 42)",
        "error_args": ["boom", 42],
    }


def test_serialize_public_error_omits_raw_exception_text() -> None:
    public_error = serialize_public_error(RuntimeError("authorization bearer-secret"))
    serialized = dumps(public_error)

    assert public_error["error_type"] == "RuntimeError"
    assert public_error["error_code"] == "RuntimeError"
    assert public_error["message"] == "An internal error occurred."
    assert public_error["retryable"] is False
    assert "bearer-secret" not in serialized


def test_redact_sensitive_data_recursively_redacts_sensitive_keys() -> None:
    redacted = redact_sensitive_data(
        {
            "api_key": "secret-key",
            "nested": {"password": "secret-password", "safe": "public"},
            "items": [{"authorization": "Bearer token-value"}],
        }
    )

    assert redacted == {
        "api_key": REDACTED,
        "nested": {"password": REDACTED, "safe": "public"},
        "items": [{"authorization": REDACTED}],
    }


def test_safe_public_jsonable_redacts_after_json_conversion() -> None:
    public_value = safe_public_jsonable(
        {"safe": _Point(1, 2), "private_data": {"token": "secret-token"}}
    )

    assert public_value == {
        "safe": {"x": 1, "y": 2},
        "private_data": REDACTED,
    }
