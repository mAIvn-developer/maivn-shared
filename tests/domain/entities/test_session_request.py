# pyright: strict
from __future__ import annotations

import json
from typing import cast

import pytest
from pydantic import ValidationError

from maivn_shared.domain.entities.messages import HumanMessage, RedactedMessage
from maivn_shared.domain.entities.session import SessionRequest

# MARK: Fixtures


def _sample_request() -> SessionRequest:
    return SessionRequest.model_validate(
        {
            "messages": [
                {"type": "human", "content": "Hello there", "id": "m1", "name": "caller"},
                {"type": "redacted", "content": "My SSN is x", "known_pii_values": ["secret-val"]},
            ],
            "tools": [
                {
                    "tool_id": "t1",
                    "agent_id": "a1",
                    "name": "search",
                    "description": "searches",
                    "args_schema": {"type": "object", "properties": {}},
                }
            ],
            "metadata": {"app": "demo"},
            "model": "fast",
        }
    )


# Golden snapshot captured from the pre-refactor serializer (heavy-6 byte-equivalence gate).
_GOLDEN_DUMP = (
    '{"force_final_tool": false, "messages": [{"additional_kwargs": {}, "content": '
    '"Hello there", "id": "m1", "name": "caller", "response_metadata": {}, "type": "human"}, '
    '{"additional_kwargs": {}, "content": "My SSN is x", "known_pii_values": ["secret-val"], '
    '"response_metadata": {}, "type": "redacted"}], "metadata": {"app": "demo"}, '
    '"model": "fast", "status_messages": false, "stream_response": true, "tools": '
    '[{"agent_id": "a1", "always_execute": false, "args_schema": {"properties": {}, "type": '
    '"object"}, "description": "searches", "final_tool": false, "metadata": {}, "name": '
    '"search", "tags": [], "tool_id": "t1", "tool_type": "func"}]}'
)


# MARK: Serializer Byte-Equivalence (heavy-6)


def test_session_request_dump_matches_golden_snapshot() -> None:
    request = _sample_request()
    dumped = json.dumps(request.model_dump(mode="json", exclude_none=True), sort_keys=True)
    assert dumped == _GOLDEN_DUMP


def test_session_request_dump_is_stable_across_repeated_calls() -> None:
    request = _sample_request()
    first = json.dumps(request.model_dump(mode="json", exclude_none=True), sort_keys=True)
    second = json.dumps(request.model_dump(mode="json", exclude_none=True), sort_keys=True)
    assert first == second


# MARK: Message Coercion (heavy-5)


def test_session_request_coerces_wire_human_message() -> None:
    request = SessionRequest.model_validate(
        {"messages": [{"type": "human", "content": "hi", "id": "abc", "name": "user-a"}]}
    )
    message = request.messages[0]
    assert isinstance(message, HumanMessage)
    payload = cast(dict[str, object], message.model_dump())
    assert payload["content"] == "hi"
    assert payload["id"] == "abc"
    assert payload["name"] == "user-a"


def test_session_request_coerces_role_alias_to_human() -> None:
    request = SessionRequest.model_validate({"messages": [{"role": "user", "content": "yo"}]})
    assert isinstance(request.messages[0], HumanMessage)


def test_session_request_coerces_wire_redacted_message() -> None:
    request = SessionRequest.model_validate(
        {"messages": [{"type": "redacted", "content": "secret", "known_pii_values": ["secret"]}]}
    )
    message = request.messages[0]
    assert isinstance(message, RedactedMessage)
    payload = cast(dict[str, object], message.model_dump())
    assert payload["content"] == "secret"


def test_session_request_preserves_existing_human_message_instance() -> None:
    original = HumanMessage(content="kept")
    request = SessionRequest(messages=[original])
    assert request.messages[0] is original


def test_session_request_passes_through_unknown_message_kind() -> None:
    request = SessionRequest.model_validate(
        {"messages": [{"type": "ai", "content": "assistant reply"}]}
    )
    message = request.messages[0]
    payload = cast(dict[str, object], message.model_dump())
    assert payload["type"] == "ai"
    assert payload["content"] == "assistant reply"


# MARK: Model Tier + Force Model Fields


def test_session_request_model_defaults_to_none() -> None:
    request = SessionRequest()
    assert request.model is None


def test_session_request_model_accepts_auto() -> None:
    request = SessionRequest(model="auto")
    assert request.model == "auto"


def test_session_request_model_accepts_fast() -> None:
    request = SessionRequest(model="fast")
    assert request.model == "fast"


def test_session_request_model_accepts_balanced() -> None:
    request = SessionRequest(model="balanced")
    assert request.model == "balanced"


def test_session_request_model_accepts_max() -> None:
    request = SessionRequest(model="max")
    assert request.model == "max"


def test_session_request_model_rejects_invalid_tier() -> None:
    with pytest.raises(ValidationError):
        SessionRequest(model="turbo")  # type: ignore[arg-type]


def test_session_request_force_model_defaults_to_none() -> None:
    request = SessionRequest()
    assert request.force_model is None


def test_session_request_force_model_accepts_string() -> None:
    request = SessionRequest(force_model="claude-opus-4-5")
    assert request.force_model == "claude-opus-4-5"


def test_session_request_force_model_excluded_when_none_in_dump() -> None:
    request = SessionRequest()
    dumped = request.model_dump(mode="json", exclude_none=True)
    assert "force_model" not in dumped


def test_session_request_force_model_included_in_dump_when_set() -> None:
    request = SessionRequest(force_model="claude-haiku-3-5")
    dumped = request.model_dump(mode="json", exclude_none=True)
    assert dumped["force_model"] == "claude-haiku-3-5"
