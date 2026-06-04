# pyright: strict
"""Message types for agent communication.

Re-exports LangChain message types for consistent usage across the codebase.
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import ClassVar, Literal, Protocol, TypeAlias, TypeGuard, cast

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.messages import (
    HumanMessage as LangChainHumanMessage,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .pii_whitelist import PIIWhitelist

# MARK: Configuration

_MAX_ATTACHMENT_BYTES = 50 * 1024 * 1024
_WIRE_ATTACHMENT_FILE_PATH_ERROR = (
    "Attachment file paths are only allowed for local constructors; "
    "wire payloads must use content_base64 or text_content."
)

# Initialize the mimetypes database once at import time so the first
# ``guess_type`` call in a request does not pay the lazy system-file scan.
mimetypes.init()


# MARK: Types

AttachmentPayload: TypeAlias = dict[str, object]
MessageContent: TypeAlias = str | list[str | dict[str, object]]


class ReadableBytesOrText(Protocol):
    """File-like object that exposes a synchronous read method."""

    def read(self) -> object: ...


# MARK: - Private Data Model


class PrivateData(BaseModel):
    """Structured known PII descriptor for enhanced redaction.

    Provides custom naming, typing, and metadata for known PII values,
    enriching the private_data_schema visible to the LLM.

    Can be used alongside raw strings in known_pii_values::

        RedactedMessage(
            content='Process claim for Maria Santos.',
            known_pii_values=[
                PrivateData(value='Maria Santos', name='patient_name', pii_type='person',
                            label='Patient Name'),
                PrivateData(value='1985-07-14', name='patient_dob', pii_type='date',
                            label='Date of Birth'),
                '212-555-0101',  # Raw strings still work
            ],
        )
    """

    value: str = Field(
        ...,
        description="The actual PII value to redact.",
    )
    name: str | None = Field(
        default=None,
        description=(
            "Custom placeholder key name. If provided, used as the private_data key "
            'instead of auto-generated pii_{type}_{n}. Example: "patient_name".'
        ),
    )
    pii_type: str | None = Field(
        default=None,
        description=(
            'PII entity type for categorization. Examples: "person", "phone", "email", '
            '"ssn", "date", "account_id". Overrides auto-inferred type from regex matching.'
        ),
    )
    label: str | None = Field(
        default=None,
        description=(
            "Human-readable label included in the private_data_schema. "
            'Example: "Patient Name", "Date of Birth".'
        ),
    )
    description: str | None = Field(
        default=None,
        description=(
            "Description of what this value represents, included in the "
            "private_data_schema for enhanced LLM context."
        ),
    )
    format: str | None = Field(
        default=None,
        description=(
            "Semantic format hint that overrides auto-inferred format in the schema. "
            'Examples: "email", "phone", "date", "ssn", "us_phone".'
        ),
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)


# MARK: - Custom Message Types


class HumanMessage(LangChainHumanMessage):
    """Human message with optional attachment payloads."""

    type: Literal["human"] = "human"

    def __init__(
        self,
        content: object,
        *,
        attachments: list[AttachmentPayload] | None = None,
        allow_attachment_file_paths: bool = True,
        **kwargs: object,
    ) -> None:
        additional_kwargs = _normalize_additional_kwargs(kwargs.pop("additional_kwargs", None))
        raw_attachments = _collect_raw_attachments(
            additional_kwargs=additional_kwargs,
            attachments=attachments,
        )
        if raw_attachments:
            additional_kwargs["attachments"] = _normalize_attachments(
                raw_attachments,
                allow_file_paths=allow_attachment_file_paths,
            )
        super().__init__(  # pyright: ignore[reportUnknownMemberType]  # langchain_core message initializers expose Any in stubs
            content=cast(MessageContent, content),
            additional_kwargs=additional_kwargs,
            **kwargs,
        )


class RedactedMessage(BaseMessage):
    """Human message with redacted placeholders.

    Stored as type="redacted" for internal processing and mapped to HumanMessage
    at LLM invocation time for provider compatibility.

    Args:
        content: Raw user text. PII detection runs on this content.
        known_pii_values: Optional list of known PII to seed redaction (raw
            strings or ``PrivateData`` objects).
        pii_whitelist: Optional ``PIIWhitelist`` describing entity categories,
            literal values, or regex patterns whose detected spans should be
            left in cleartext. Whitelist application is audited end-to-end.
        attachments: Optional list of attachment payloads.
    """

    type: str = "redacted"
    known_pii_values: list[str | PrivateData] | None = None
    pii_whitelist: PIIWhitelist | None = None

    def __init__(
        self,
        content: object,
        *,
        attachments: list[AttachmentPayload] | None = None,
        allow_attachment_file_paths: bool = True,
        **kwargs: object,
    ) -> None:
        additional_kwargs = _normalize_additional_kwargs(kwargs.pop("additional_kwargs", None))
        known_pii_values = normalize_known_pii_values(kwargs.pop("known_pii_values", None))
        pii_whitelist = _normalize_pii_whitelist(kwargs.pop("pii_whitelist", None))
        raw_attachments = _collect_raw_attachments(
            additional_kwargs=additional_kwargs,
            attachments=attachments,
        )
        if raw_attachments:
            additional_kwargs["attachments"] = _normalize_attachments(
                raw_attachments,
                allow_file_paths=allow_attachment_file_paths,
            )
        super().__init__(  # pyright: ignore[reportUnknownMemberType]  # langchain_core BaseMessage initializer exposes Any in stubs
            content=cast(MessageContent, content),
            additional_kwargs=additional_kwargs,
            known_pii_values=known_pii_values,
            pii_whitelist=pii_whitelist,
            **kwargs,
        )


# MARK: - Helpers


def _normalize_additional_kwargs(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        payload = cast(dict[object, object], value)
        return cast(dict[str, object], payload.copy())
    return {}


def _normalize_pii_whitelist(value: object) -> PIIWhitelist | None:
    if value is None:
        return None
    if isinstance(value, PIIWhitelist):
        return value
    if isinstance(value, dict):
        return PIIWhitelist.model_validate(cast(dict[str, object], value))
    raise TypeError("pii_whitelist must be a PIIWhitelist instance, dict, or None")


def normalize_known_pii_values(value: object) -> list[str | PrivateData] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise TypeError("known_pii_values must be a list of strings/PrivateData or None")

    normalized: list[str | PrivateData] = []
    seen: set[str] = set()
    for item in cast(list[object], value):
        if isinstance(item, PrivateData):
            candidate_value = item.value.strip()
            if not candidate_value or candidate_value in seen:
                continue
            seen.add(candidate_value)
            if candidate_value != item.value:
                item = PrivateData(
                    value=candidate_value,
                    name=item.name,
                    pii_type=item.pii_type,
                    label=item.label,
                    description=item.description,
                    format=item.format,
                )
            normalized.append(item)
        elif isinstance(item, dict) and "value" in item:
            try:
                pd = PrivateData.model_validate(cast(dict[str, object], item))
            except ValidationError as err:
                raise TypeError("known_pii_values dict entries must be valid PrivateData") from err
            candidate_value = pd.value.strip()
            if not candidate_value or candidate_value in seen:
                continue
            seen.add(candidate_value)
            if candidate_value != pd.value:
                pd = PrivateData(
                    value=candidate_value,
                    name=pd.name,
                    pii_type=pd.pii_type,
                    label=pd.label,
                    description=pd.description,
                    format=pd.format,
                )
            normalized.append(pd)
        elif isinstance(item, str):
            candidate = item.strip()
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            normalized.append(candidate)
        else:
            raise TypeError("known_pii_values entries must be strings or PrivateData")
    return normalized or None


def _collect_raw_attachments(
    *,
    additional_kwargs: dict[str, object],
    attachments: object,
) -> list[AttachmentPayload]:
    raw: list[AttachmentPayload] = []
    nested = additional_kwargs.get("attachments")
    if isinstance(nested, list):
        raw.extend(
            cast(AttachmentPayload, cast(dict[object, object], item).copy())
            for item in cast(list[object], nested)
            if isinstance(item, dict)
        )
    if isinstance(attachments, list):
        raw.extend(
            cast(AttachmentPayload, cast(dict[object, object], item).copy())
            for item in cast(list[object], attachments)
            if isinstance(item, dict)
        )
    return raw


def _normalize_attachments(
    raw_attachments: list[AttachmentPayload],
    *,
    allow_file_paths: bool,
) -> list[AttachmentPayload]:
    normalized: list[AttachmentPayload] = []
    for attachment in raw_attachments:
        normalized.append(_normalize_attachment(attachment, allow_file_paths=allow_file_paths))
    return normalized


def _normalize_attachment(
    attachment: AttachmentPayload,
    *,
    allow_file_paths: bool,
) -> AttachmentPayload:
    payload = dict(attachment)

    content_bytes = _extract_attachment_bytes(payload, allow_file_paths=allow_file_paths)
    if not content_bytes:
        raise ValueError("Attachment content is required")
    if len(content_bytes) > _MAX_ATTACHMENT_BYTES:
        raise ValueError("Attachment exceeds maximum supported size")

    name = _resolve_attachment_name(payload) or "attachment.bin"
    mime_type = _resolve_mime_type(name=name, payload=payload)
    output: AttachmentPayload = {
        "name": name,
        "mime_type": mime_type,
        "content_base64": base64.b64encode(content_bytes).decode("ascii"),
    }

    for key in ("sharing_scope", "description", "source_url", "binding_type", "source_type"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            output[key] = value.strip()

    tags = payload.get("tags")
    if isinstance(tags, list):
        normalized_tags = [str(tag).strip() for tag in cast(list[object], tags) if str(tag).strip()]
        if normalized_tags:
            output["tags"] = normalized_tags

    return output


def _extract_attachment_bytes(payload: AttachmentPayload, *, allow_file_paths: bool) -> bytes:
    content_base64 = payload.get("content_base64")
    if isinstance(content_base64, str) and content_base64.strip():
        try:
            return base64.b64decode(content_base64, validate=True)
        except (TypeError, ValueError) as exc:
            raise ValueError("Attachment content_base64 is invalid") from exc

    content_bytes = payload.get("content_bytes")
    if isinstance(content_bytes, bytes):
        return content_bytes
    if isinstance(content_bytes, bytearray):
        return bytes(content_bytes)

    text_content = payload.get("text_content")
    if isinstance(text_content, str):
        return text_content.encode("utf-8")

    file_value = payload.get("file")
    if file_value is None:
        return b""

    if isinstance(file_value, bytes):
        return file_value
    if isinstance(file_value, bytearray):
        return bytes(file_value)
    if isinstance(file_value, str | Path):
        if not allow_file_paths:
            raise ValueError(_WIRE_ATTACHMENT_FILE_PATH_ERROR)
        file_path = Path(file_value)
        if file_path.exists() and file_path.is_file():
            return file_path.read_bytes()
        raise ValueError(f"Attachment file not found: {file_path}")
    if _is_readable(file_value):
        raw = file_value.read()
        if isinstance(raw, str):
            return raw.encode("utf-8")
        if isinstance(raw, bytes):
            return raw
        raise ValueError("Attachment file handle returned unsupported type")
    return b""


def _resolve_attachment_name(payload: AttachmentPayload) -> str | None:
    for key in ("name", "filename"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return _sanitize_filename(value)

    file_value = payload.get("file")
    if isinstance(file_value, str | Path):
        return _sanitize_filename(Path(file_value).name)
    candidate_name = getattr(file_value, "name", None)
    if isinstance(candidate_name, str) and candidate_name.strip():
        return _sanitize_filename(Path(candidate_name).name)
    return None


def _resolve_mime_type(*, name: str, payload: AttachmentPayload) -> str:
    explicit = payload.get("mime_type")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    guessed, _ = mimetypes.guess_type(name)
    return guessed or "application/octet-stream"


def _is_readable(value: object) -> TypeGuard[ReadableBytesOrText]:
    return callable(getattr(value, "read", None))


def _sanitize_filename(value: str) -> str:
    name = value.replace("\\", "/").split("/")[-1].strip()
    if not name:
        return "attachment.bin"
    return name[:255]


# MARK: - Public API

__all__ = [
    "AIMessage",
    "BaseMessage",
    "HumanMessage",
    "PrivateData",
    "RedactedMessage",
    "SystemMessage",
    "ToolMessage",
]
