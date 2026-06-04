# pyright: strict
from __future__ import annotations

import json

from maivn_shared.domain.exceptions import MaivnError


def test_public_error_serialization_excludes_context_cause_and_args() -> None:
    error = MaivnError(
        "raw message contains api-secret",
        context={"api_key": "secret-key"},
        cause=RuntimeError("cause contains refresh-token"),
    )

    public_error = error.to_public_dict()
    serialized = json.dumps(public_error)

    assert public_error == {
        "error_type": "MaivnError",
        "error_code": "MaivnError",
        "message": "An internal error occurred.",
        "retryable": False,
    }
    assert "api-secret" not in serialized
    assert "secret-key" not in serialized
    assert "refresh-token" not in serialized


def test_internal_error_dict_redacts_context_and_omits_raw_cause() -> None:
    error = MaivnError(
        "diagnostic message",
        context={"access_token": "secret-token", "safe": "public"},
        cause=RuntimeError("cause contains private data"),
    )

    internal_error = error.to_dict()
    serialized = json.dumps(internal_error)

    assert internal_error["context"] == {"access_token": "[REDACTED]", "safe": "public"}
    assert internal_error["cause"] == "RuntimeError"
    assert "secret-token" not in serialized
    assert "private data" not in serialized
