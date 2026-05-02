from __future__ import annotations

import base64

import pytest

from maivn_shared.domain.entities.messages import HumanMessage, PrivateData, RedactedMessage
from maivn_shared.domain.entities.session import RedactionPreviewRequest, SessionRequest


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

    payload = message.model_dump(exclude_none=True)
    attachments = payload["additional_kwargs"]["attachments"]
    assert len(attachments) == 1
    assert attachments[0]["name"] == "notes.txt"
    assert attachments[0]["mime_type"] == "text/plain"
    assert base64.b64decode(attachments[0]["content_base64"]) == b"hello world"


def test_human_message_serializes_attachment_file_path(tmp_path) -> None:
    path = tmp_path / "policy.md"
    path.write_text("policy content", encoding="utf-8")

    message = HumanMessage(
        content="Use attached policy.",
        attachments=[{"file": str(path)}],
    )

    payload = message.model_dump(exclude_none=True)
    attachment = payload["additional_kwargs"]["attachments"][0]
    assert attachment["name"] == "policy.md"
    assert base64.b64decode(attachment["content_base64"]) == b"policy content"


def test_redacted_message_supports_attachments() -> None:
    message = RedactedMessage(
        content="My SSN is {_{{private_ssn}}_}.",
        attachments=[{"name": "secure.txt", "text_content": "classified"}],
        additional_kwargs={"metadata": {"message_type": "redacted"}},
    )

    payload = message.model_dump(exclude_none=True)
    attachments = payload["additional_kwargs"]["attachments"]
    assert len(attachments) == 1
    assert base64.b64decode(attachments[0]["content_base64"]) == b"classified"
    assert payload["additional_kwargs"]["metadata"]["message_type"] == "redacted"


def test_redacted_message_normalizes_known_pii_values() -> None:
    message = RedactedMessage(
        content="Email me at alice@example.com.",
        known_pii_values=[" alice@example.com ", "bob@example.com", "alice@example.com", ""],
    )

    payload = message.model_dump(exclude_none=True)
    assert payload["known_pii_values"] == ["alice@example.com", "bob@example.com"]


def test_redacted_message_strips_private_data_and_dict_known_pii_values() -> None:
    message = RedactedMessage(
        content="Email me at alice@example.com.",
        known_pii_values=[
            PrivateData(value=" alice@example.com ", name="primary_email"),
            {"value": " bob@example.com ", "name": "backup_email"},
        ],
    )

    payload = message.model_dump(exclude_none=True)
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

    assert request.model_dump(exclude_none=True)["known_pii_values"] == [
        {"value": "alice@example.com", "name": "primary_email"},
        {"value": "bob@example.com", "name": "backup_email"},
    ]


def test_human_message_rejects_missing_attachment_content() -> None:
    with pytest.raises(ValueError):
        HumanMessage(content="No content", attachments=[{"name": "empty.txt"}])


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
    payload = request.messages[0].model_dump(exclude_none=True)
    attachments = payload["additional_kwargs"]["attachments"]
    assert len(attachments) == 1
    assert attachments[0]["name"] == "notes.txt"
    assert attachments[0]["mime_type"] == "text/plain"
    assert base64.b64decode(attachments[0]["content_base64"]) == b"from wire payload"


def test_session_request_rejects_attachment_file_path_from_payload(tmp_path) -> None:
    path = tmp_path / "server-secret.txt"
    path.write_text("do not read", encoding="utf-8")

    with pytest.raises(ValueError, match="file paths"):
        SessionRequest.model_validate(
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
    payload = request.messages[0].model_dump(exclude_none=True)
    attachments = payload["additional_kwargs"]["attachments"]
    assert len(attachments) == 1
    assert base64.b64decode(attachments[0]["content_base64"]) == b"classified payload"
    assert payload["additional_kwargs"]["metadata"]["message_type"] == "redacted"


def test_redaction_preview_rejects_attachment_file_path_from_payload(tmp_path) -> None:
    path = tmp_path / "preview-secret.txt"
    path.write_text("do not read", encoding="utf-8")

    with pytest.raises(ValueError, match="file paths"):
        RedactionPreviewRequest.model_validate(
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
    serialized = request.model_dump(mode="json", exclude_none=True)
    assert serialized["messages"][0]["known_pii_values"] == ["alice@example.com", "bob@example.com"]


def test_session_request_rejects_reserved_memory_metadata_keys() -> None:
    with pytest.raises(ValueError, match="use memory_config instead"):
        SessionRequest(
            messages=[],
            metadata={"memory_level": "glimpse"},
        )


def test_session_request_rejects_reserved_session_control_metadata_keys() -> None:
    with pytest.raises(ValueError, match="use typed session config fields instead"):
        SessionRequest(
            messages=[],
            metadata={
                "allowed_system_tools": ["web_search"],
                "allow_reevaluate_loop": True,
                "client_timezone": "America/Chicago",
                "max_orchestration_cycles": 2,
            },
        )
