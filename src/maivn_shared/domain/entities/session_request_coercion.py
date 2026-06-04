# pyright: strict
"""Coercion helpers that normalize wire message payloads into typed messages."""

from __future__ import annotations

from typing import TypeAlias, cast

from .messages import BaseMessage, HumanMessage, RedactedMessage

# MARK: Types

ObjectDict: TypeAlias = dict[str, object]
AttachmentPayload: TypeAlias = dict[str, object]


# MARK: Helpers


def _coerce_message_kind(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if not normalized:
        return None
    if normalized == "user":
        return "human"
    if normalized == "assistant":
        return "ai"
    return normalized


def _extract_message_common_kwargs(payload: ObjectDict) -> ObjectDict:
    kwargs: ObjectDict = {}

    identifier = payload.get("id")
    if isinstance(identifier, str) and identifier.strip():
        kwargs["id"] = identifier

    name = payload.get("name")
    if isinstance(name, str) and name.strip():
        kwargs["name"] = name

    response_metadata = payload.get("response_metadata")
    if isinstance(response_metadata, dict):
        kwargs["response_metadata"] = response_metadata

    return kwargs


# MARK: Public Coercion API


def normalize_attachment_payloads(value: object) -> list[AttachmentPayload] | None:
    if not isinstance(value, list):
        return None
    return [
        cast(AttachmentPayload, cast(dict[object, object], item).copy())
        for item in cast(list[object], value)
        if isinstance(item, dict)
    ]


def coerce_human_or_redacted_message(value: object) -> object:
    if isinstance(value, HumanMessage | RedactedMessage):
        return value

    payload: ObjectDict | None = None
    if isinstance(value, BaseMessage):
        # BaseMessage is a langchain_core Pydantic model, so model_dump always
        # returns a dict; no getattr fallback is reachable.
        payload = cast(ObjectDict, value.model_dump(exclude_none=True))
    elif isinstance(value, dict):
        payload = cast(ObjectDict, cast(dict[object, object], value).copy())

    if payload is None:
        return cast(object, value)

    message_kind = _coerce_message_kind(payload.get("type"))
    if message_kind is None:
        message_kind = _coerce_message_kind(payload.get("role"))
    if message_kind not in {"human", "redacted"}:
        return cast(object, value)

    content = payload.get("content")
    if content is None:
        content = ""

    additional_kwargs = payload.get("additional_kwargs")
    attachments = payload.get("attachments")
    normalized_attachments = normalize_attachment_payloads(attachments)
    common_kwargs = _extract_message_common_kwargs(payload)

    if message_kind == "redacted":
        return RedactedMessage(
            content=content,
            attachments=normalized_attachments,
            allow_attachment_file_paths=False,
            additional_kwargs=additional_kwargs,
            known_pii_values=payload.get("known_pii_values"),
            **common_kwargs,
        )

    return HumanMessage(
        content=content,
        attachments=normalized_attachments,
        allow_attachment_file_paths=False,
        additional_kwargs=additional_kwargs,
        **common_kwargs,
    )


__all__ = [
    "coerce_human_or_redacted_message",
    "normalize_attachment_payloads",
]
