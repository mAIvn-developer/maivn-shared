# pyright: strict
from __future__ import annotations

import base64
from pathlib import Path
from typing import Literal, cast

import pytest
from pydantic import BaseModel

from maivn_shared.domain.entities.messages import HumanMessage, PrivateData, RedactedMessage
from maivn_shared.domain.entities.session import RedactionPreviewRequest, SessionRequest

# MARK: Helpers


def _payload(model: BaseModel, *, mode: Literal["json", "python"] = "python") -> dict[str, object]:
    return cast(dict[str, object], cast(object, model.model_dump(mode=mode, exclude_none=True)))


def _attachments(payload: dict[str, object]) -> list[dict[str, object]]:
    additional_kwargs = cast(dict[str, object], payload["additional_kwargs"])
    return cast(list[dict[str, object]], additional_kwargs["attachments"])


def _metadata(payload: dict[str, object]) -> dict[str, object]:
    additional_kwargs = cast(dict[str, object], payload["additional_kwargs"])
    return cast(dict[str, object], additional_kwargs["metadata"])


def _decoded_content(attachment: dict[str, object]) -> bytes:
    return base64.b64decode(cast(str, attachment["content_base64"]))


# MARK: Tests


def test_human_message_serializes_attachment_bytes() -> None:
    message = HumanMessage(
        content="Please review the attachment.",
        attachments=[
            {
                "name": "notes.txt",
                "file": b"hello world",
                "mime_type": "text/plain",
                "tags": ["notes", "demo"],
            }
        ],
    )

    payload = _payload(message)
    attachments = _attachments(payload)
    assert len(attachments) == 1
    assert attachments[0]["name"] == "notes.txt"
    assert attachments[0]["mime_type"] == "text/plain"
    assert _decoded_content(attachments[0]) == b"hello world"


def test_human_message_serializes_attachment_file_path(tmp_path: Path) -> None:
    path = tmp_path / "policy.md"
    _ = path.write_text("policy content", encoding="utf-8")

    message = HumanMessage(
        content="Use attached policy.",
        attachments=[{"file": str(path)}],
    )

    payload = _payload(message)
    attachment = _attachments(payload)[0]
    assert attachment["name"] == "policy.md"
    assert _decoded_content(attachment) == b"policy content"


def test_redacted_message_supports_attachments() -> None:
    message = RedactedMessage(
        content="My SSN is {_{{private_ssn}}_}.",
        attachments=[{"name": "secure.txt", "text_content": "classified"}],
        additional_kwargs={"metadata": {"message_type": "redacted"}},
    )

    payload = _payload(message)
    attachments = _attachments(payload)
    assert len(attachments) == 1
    assert _decoded_content(attachments[0]) == b"classified"
    assert _metadata(payload)["message_type"] == "redacted"


def test_redacted_message_normalizes_known_pii_values() -> None:
    message = RedactedMessage(
        content="Email me at alice@example.com.",
        known_pii_values=[" alice@example.com ", "bob@example.com", "alice@example.com", ""],
    )

    payload = _payload(message)
    assert payload["known_pii_values"] == ["alice@example.com", "bob@example.com"]


def test_redacted_message_strips_private_data_and_dict_known_pii_values() -> None:
    message = RedactedMessage(
        content="Email me at alice@example.com.",
        known_pii_values=[
            PrivateData(value=" alice@example.com ", name="primary_email"),
            {"value": " bob@example.com ", "name": "backup_email"},
        ],
    )

    payload = _payload(message)
    assert payload["known_pii_values"] == [
        {"value": "alice@example.com", "name": "primary_email"},
        {"value": "bob@example.com", "name": "backup_email"},
    ]


def test_redaction_preview_request_strips_private_data_and_dict_known_pii_values() -> None:
    request = RedactionPreviewRequest.model_validate(
        {
            "message": RedactedMessage(content="Email me at alice@example.com."),
            "known_pii_values": [
                PrivateData(value=" alice@example.com ", name="primary_email"),
                {"value": " bob@example.com ", "name": "backup_email"},
            ],
        }
    )

    assert _payload(request)["known_pii_values"] == [
        {"value": "alice@example.com", "name": "primary_email"},
        {"value": "bob@example.com", "name": "backup_email"},
    ]


def test_human_message_rejects_missing_attachment_content() -> None:
    with pytest.raises(ValueError):
        _ = HumanMessage(content="No content", attachments=[{"name": "empty.txt"}])


def test_human_message_surfaces_missing_attachment_file_path(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.txt"
    with pytest.raises(ValueError, match="not found"):
        _ = HumanMessage(content="Attach.", attachments=[{"file": str(missing)}])


def test_human_message_surfaces_unsupported_file_handle() -> None:
    class _BadHandle:
        def read(self) -> object:
            return 123

    with pytest.raises(ValueError, match="unsupported"):
        _ = HumanMessage(content="Attach.", attachments=[{"file": _BadHandle()}])


def test_session_request_normalizes_human_message_attachments() -> None:
    request = SessionRequest.model_validate(
        {
            "messages": [
                {
                    "type": "human",
                    "content": "Please index this file.",
                    "attachments": [
                        {
                            "name": "notes.txt",
                            "text_content": "from wire payload",
                            "mime_type": "text/plain",
                        }
                    ],
                }
            ]
        }
    )

    assert isinstance(request.messages[0], HumanMessage)
    payload = _payload(request.messages[0])
    attachments = _attachments(payload)
    assert len(attachments) == 1
    assert attachments[0]["name"] == "notes.txt"
    assert attachments[0]["mime_type"] == "text/plain"
    assert _decoded_content(attachments[0]) == b"from wire payload"


def test_session_request_rejects_attachment_file_path_from_payload(tmp_path: Path) -> None:
    path = tmp_path / "server-secret.txt"
    _ = path.write_text("do not read", encoding="utf-8")

    with pytest.raises(ValueError, match="file paths"):
        _ = SessionRequest.model_validate(
            {
                "messages": [
                    {
                        "type": "human",
                        "content": "Attach this.",
                        "attachments": [{"file": str(path)}],
                    }
                ]
            }
        )


def test_session_request_normalizes_redacted_message_attachments() -> None:
    request = SessionRequest.model_validate(
        {
            "messages": [
                {
                    "type": "redacted",
                    "content": "My SSN is {_{{private_ssn}}_}.",
                    "additional_kwargs": {
                        "metadata": {"message_type": "redacted"},
                        "attachments": [
                            {
                                "name": "secure.txt",
                                "text_content": "classified payload",
                            }
                        ],
                    },
                }
            ]
        }
    )

    assert isinstance(request.messages[0], RedactedMessage)
    payload = _payload(request.messages[0])
    attachments = _attachments(payload)
    assert len(attachments) == 1
    assert _decoded_content(attachments[0]) == b"classified payload"
    assert _metadata(payload)["message_type"] == "redacted"


def test_redaction_preview_rejects_attachment_file_path_from_payload(tmp_path: Path) -> None:
    path = tmp_path / "preview-secret.txt"
    _ = path.write_text("do not read", encoding="utf-8")

    with pytest.raises(ValueError, match="file paths"):
        _ = RedactionPreviewRequest.model_validate(
            {
                "message": {
                    "type": "redacted",
                    "content": "Preview attachment.",
                    "additional_kwargs": {"attachments": [{"file": str(path)}]},
                }
            }
        )


def test_session_request_preserves_redacted_message_known_pii_values_in_payload() -> None:
    request = SessionRequest.model_validate(
        {
            "messages": [
                {
                    "type": "redacted",
                    "content": "Email me at alice@example.com.",
                    "known_pii_values": [
                        "alice@example.com",
                        "bob@example.com",
                        "alice@example.com",
                    ],
                }
            ]
        }
    )

    assert isinstance(request.messages[0], RedactedMessage)
    serialized = _payload(request, mode="json")
    messages = cast(list[dict[str, object]], serialized["messages"])
    assert messages[0]["known_pii_values"] == ["alice@example.com", "bob@example.com"]


def test_session_request_rejects_reserved_memory_metadata_keys() -> None:
    with pytest.raises(ValueError, match="use memory_config instead"):
        _ = SessionRequest(
            messages=[],
            metadata={"memory_level": "glimpse"},
        )


def test_session_request_rejects_reserved_session_control_metadata_keys() -> None:
    with pytest.raises(ValueError, match="use typed session config fields instead"):
        _ = SessionRequest(
            messages=[],
            metadata={
                "allowed_system_tools": ["web_search"],
                "allow_reevaluate_loop": True,
                "client_timezone": "America/Chicago",
                "max_orchestration_cycles": 2,
            },
        )
