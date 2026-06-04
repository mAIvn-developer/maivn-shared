# pyright: strict
from __future__ import annotations

from maivn_shared.domain.entities.session import SessionResponse

# MARK: Serialization


def test_session_response_includes_computed_response_in_model_dump() -> None:
    response = SessionResponse(responses=["hello"])

    payload = response.model_dump()

    assert payload["responses"] == ["hello"]
    assert payload["response"] == "hello"
