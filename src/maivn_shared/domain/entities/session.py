"""Session-related data models shared across projects."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field, field_serializer, field_validator

from ...core.data.id_generator import create_uuid
from ...utils.token_models import TokenUsage
from .memory_config import MemoryConfig, is_reserved_memory_metadata_key
from .messages import (
    BaseMessage,
    HumanMessage,
    PrivateData,
    RedactedMessage,
    normalize_known_pii_values,
)
from .pii_whitelist import PIIWhitelist
from .session_config import (
    MemoryAssetsConfig,
    SessionExecutionConfig,
    SessionOrchestrationConfig,
    StructuredOutputConfig,
    SwarmConfig,
    SystemToolsConfig,
    is_reserved_session_config_metadata_key,
)
from .tool_spec import ToolSpec

# MARK: Session Request


SWARM_INVOCATION_INTENT_METADATA_KEY = "swarm_invocation_intent"
SWARM_AGENT_INVOCATION_METADATA_KEY = "swarm_agent_invocation"


def _coerce_message_kind(value: Any) -> str | None:
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


def _extract_message_common_kwargs(payload: dict[str, Any]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}

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


def _coerce_human_or_redacted_message(value: Any) -> BaseMessage | Any:
    if isinstance(value, HumanMessage | RedactedMessage):
        return value

    payload: dict[str, Any] | None = None
    if isinstance(value, BaseMessage):
        if hasattr(value, "model_dump"):
            dumped = value.model_dump(exclude_none=True)
            if isinstance(dumped, dict):
                payload = dumped
        if payload is None:
            payload = {
                "type": getattr(value, "type", None),
                "content": getattr(value, "content", ""),
            }
            additional_kwargs = getattr(value, "additional_kwargs", None)
            if isinstance(additional_kwargs, dict):
                payload["additional_kwargs"] = additional_kwargs
    elif isinstance(value, dict):
        payload = dict(value)

    if payload is None:
        return value

    message_kind = _coerce_message_kind(payload.get("type"))
    if message_kind is None:
        message_kind = _coerce_message_kind(payload.get("role"))
    if message_kind not in {"human", "redacted"}:
        return value

    content = payload.get("content")
    if content is None:
        content = ""

    additional_kwargs = payload.get("additional_kwargs")
    attachments = payload.get("attachments")
    normalized_attachments = attachments if isinstance(attachments, list) else None
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


class SessionRequest(BaseModel):
    """Request model for starting a session.

    This model captures the logical inputs required to start a session
    (messages, tools, and high-level execution options). It is intentionally
    free of transport-specific concerns so it can be reused across SDKs and
    services.
    """

    messages: list[BaseMessage] = Field(
        default_factory=list,
        description="List of messages to send to the agent at session start.",
    )
    tools: list[ToolSpec] = Field(
        default_factory=list,
        description="List of tool specifications to register with the agent.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional application metadata to associate with the session. "
            "Reserved runtime-control keys are not allowed here; use typed config fields instead."
        ),
    )
    memory_config: MemoryConfig | None = Field(
        default=None,
        description=(
            "Optional typed memory configuration for retrieval, summarization, "
            "and persistence behavior."
        ),
    )
    execution_config: SessionExecutionConfig | None = Field(
        default=None,
        description="Typed SDK execution metadata such as agent identity and timeout.",
    )
    system_tools_config: SystemToolsConfig | None = Field(
        default=None,
        description="Typed server-side system tool availability and approval controls.",
    )
    structured_output_config: StructuredOutputConfig | None = Field(
        default=None,
        description="Typed structured-output transport intent.",
    )
    orchestration_config: SessionOrchestrationConfig | None = Field(
        default=None,
        description="Typed orchestration loop controls.",
    )
    memory_assets_config: MemoryAssetsConfig | None = Field(
        default=None,
        description="Typed user-defined memory skills and bound resources.",
    )
    swarm_config: SwarmConfig | None = Field(
        default=None,
        description="Typed swarm orchestration transport configuration.",
    )
    force_final_tool: bool = Field(
        default=False,
        description=(
            "If True, the agent returns the result from the tool marked with final_tool=True. "
            "If False (default), the agent returns completed leaf outputs, and may return a "
            "final_tool result if it was executed by the flow."
        ),
    )
    targeted_tools: list[str] | None = Field(
        default=None,
        description=(
            "List of tool names to execute. Returns list of results for these tools only. "
            "The agent will automatically include all dependencies. "
            "Mutually exclusive with force_final_tool."
        ),
    )
    model: Literal["fast", "balanced", "max"] | None = Field(
        default=None,
        description="LLM model selection: 'fast', 'balanced', 'max'. Defaults to 'fast'.",
    )
    reasoning: Literal["minimal", "low", "medium", "high"] | None = Field(
        default=None,
        description="Reasoning level: 'minimal', 'low', 'medium', 'high'. Affects LLM depth.",
    )
    stream_response: bool = Field(
        default=True,
        description=(
            "If True, stream synthesized response updates when supported "
            "by the runtime. Does not control status messages — use "
            "``status_messages`` for that."
        ),
    )
    status_messages: bool = Field(
        default=False,
        description=(
            "If True, emit status messages at swarm lifecycle milestones "
            "(post-planning, pre-synthesis, re-evaluation). Must be "
            "explicitly enabled via ``stream(status_messages=True)``. "
            "Automatically suppressed when ``structured_output`` is active."
        ),
    )
    max_results: int | None = Field(
        default=None,
        description="Maximum number of tools to return from semantic search.",
    )
    private_data: dict[str, Any] | None = Field(
        default=None,
        description="Private user-provided context data for resolving data dependencies.",
    )
    pii_whitelist: PIIWhitelist | None = Field(
        default=None,
        description=(
            "Optional PII whitelist that suppresses redaction of approved spans. "
            "Applied at L1 ingest, L2 tool-result scan, and audited end-to-end. "
            "Use ``phi_mode=True`` to forbid HIPAA Safe Harbor entity_type "
            "entries when handling PHI."
        ),
    )
    interrupt_data_keys: list[str] | None = Field(
        default=None,
        description=(
            "List of private_data keys that were collected via user interrupts "
            "(@depends_on_user_input)."
        ),
    )

    @field_validator("messages", mode="before")
    @classmethod
    def _normalize_messages(cls, value: Any) -> Any:
        if value is None:
            return []
        if not isinstance(value, list):
            return value
        return [_coerce_human_or_redacted_message(item) for item in value]

    @field_validator("metadata")
    @classmethod
    def _reject_reserved_config_metadata_keys(cls, value: Any) -> Any:
        if value is None or not isinstance(value, dict):
            return value
        reserved_memory_keys = sorted(
            key for key in value if isinstance(key, str) and is_reserved_memory_metadata_key(key)
        )
        if reserved_memory_keys:
            joined = ", ".join(reserved_memory_keys)
            raise ValueError(
                "Reserved memory metadata keys are not allowed in metadata; "
                f"use memory_config instead ({joined})"
            )
        reserved_session_keys = sorted(
            key
            for key in value
            if isinstance(key, str) and is_reserved_session_config_metadata_key(key)
        )
        if reserved_session_keys:
            joined = ", ".join(reserved_session_keys)
            raise ValueError(
                "Reserved session-control metadata keys are not allowed in metadata; "
                f"use typed session config fields instead ({joined})"
            )
        return value

    @field_serializer("tools", when_used="always")
    def _serialize_tools(self, tools: list[ToolSpec]) -> list[dict[str, Any]]:
        return [tool.model_dump() for tool in tools]

    @field_serializer("messages", when_used="always")
    def _serialize_messages(self, messages: list[BaseMessage]) -> list[dict[str, Any]]:
        return [message.model_dump(mode="json", exclude_none=True) for message in messages]


class SessionStartRequest(BaseModel):
    """Wire-level payload for starting a session over HTTP or other transports.

    This model wraps a :class:`SessionRequest` together with client metadata
    such as ``client_id`` and optional ``thread_id``. It is transport-friendly
    and can be used directly as the body schema for APIs that start sessions.
    """

    state: SessionRequest = Field(
        ...,
        description="Logical session request describing messages, tools, and execution options.",
    )
    client_id: str = Field(
        ...,
        description=(
            "Identifier for the SDK or client instance initiating the session. "
            "This is opaque to the core system and used only for diagnostics "
            "or correlation."
        ),
    )
    thread_id: str | None = Field(
        default=None,
        description=(
            "Optional client-defined thread identifier used to correlate multiple "
            "sessions that share a logical conversation."
        ),
    )


# MARK: Redaction Preview


class RedactionPreviewRequest(BaseModel):
    """Wire-level payload for previewing message redaction before invocation."""

    message: RedactedMessage = Field(
        ...,
        description="RedactedMessage candidate to inspect and normalize on the server.",
    )
    private_data: dict[str, Any] | None = Field(
        default=None,
        description="Optional existing private_data to merge with newly redacted values.",
    )
    known_pii_values: list[str | PrivateData] | None = Field(
        default=None,
        description=(
            "Optional caller-supplied PII values that must be redacted if found. "
            "Accepts raw strings or PrivateData objects for enhanced metadata."
        ),
    )

    @field_validator("message", mode="before")
    @classmethod
    def _normalize_redacted_message(cls, value: Any) -> Any:
        if isinstance(value, RedactedMessage):
            return value
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        content = payload.pop("content", "")
        attachments = payload.pop("attachments", None)
        additional_kwargs = payload.pop("additional_kwargs", None)
        return RedactedMessage(
            content=content,
            attachments=attachments if isinstance(attachments, list) else None,
            allow_attachment_file_paths=False,
            additional_kwargs=additional_kwargs,
            **payload,
        )

    @field_validator("known_pii_values", mode="before")
    @classmethod
    def _normalize_known_pii_values(cls, value: Any) -> list[str | PrivateData] | None:
        return normalize_known_pii_values(value)


class RedactionPreviewResponse(BaseModel):
    """Structured result returned from the redaction preview API."""

    message: RedactedMessage = Field(
        ...,
        description="Updated RedactedMessage with placeholders and redaction metadata applied.",
    )
    inserted_keys: list[str] = Field(
        default_factory=list,
        description="Private-data keys inserted into the redacted message content.",
    )
    added_private_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Only the private_data entries added by this preview operation.",
    )
    merged_private_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Full private_data after merging existing and newly added values.",
    )
    redacted_message_count: int = Field(
        default=0,
        description="Number of messages that required redaction in this preview.",
    )
    redacted_value_count: int = Field(
        default=0,
        description="Number of placeholder substitutions applied in this preview.",
    )
    matched_known_pii_values: list[str] = Field(
        default_factory=list,
        description="Subset of caller-provided known PII values that were found and redacted.",
    )
    unmatched_known_pii_values: list[str] = Field(
        default_factory=list,
        description="Caller-provided known PII values that were not found in the message content.",
    )


# MARK: Session Startup Response


class SessionStartupResponse(BaseModel):
    """Response model for session initialization."""

    session_id: str = Field(
        default_factory=create_uuid,
        description="Unique identifier for the session.",
    )
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when the session was created.",
    )


# MARK: Session Response


class SessionResponse(BaseModel):
    """Response model for session information."""

    session_id: str = Field(
        default_factory=create_uuid,
        description="Unique identifier for the session.",
    )
    assistant_id: str | None = Field(
        default=None,
        description="Assistant identifier associated with the session.",
    )
    thread_id: str | None = Field(
        default=None,
        description="Thread identifier assigned by LangGraph (if available).",
    )
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when the session was created.",
    )
    completed_at: str | None = Field(
        default=None,
        description="Timestamp when the session was completed (if applicable).",
    )
    messages: list[BaseMessage] = Field(
        default_factory=list,
        description="List of messages exchanged between the agent and the client.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Metadata associated with the session (if available).",
    )
    result: Any | None = Field(
        default=None,
        description="Result of the session (if applicable).",
    )
    responses: list[str] = Field(
        default_factory=list,
        description=(
            "Assistant response texts emitted during the session, including status messages "
            "and the final synthesized response. This is distinct from "
            "`result`, which contains tool-generated outputs."
        ),
    )
    error: str | None = Field(
        default=None,
        description="Error message if the session failed.",
    )
    status: (
        Literal["pending", "running", "waiting_for_tools", "completed", "failed", "interrupted"]
        | None
    ) = Field(
        default=None,
        description="Current status of the session execution.",
    )
    token_usage: TokenUsage | None = Field(
        default=None,
        description="Token usage summary for the session (scrubbed for client privacy).",
    )

    @computed_field
    @property
    def response(self) -> str | None:
        if not self.responses:
            return None
        return self.responses[-1]


# MARK: Tool Resume


class ToolResumePayload(BaseModel):
    """Payload for resuming a session with a single completed tool result.

    This model is used by orchestration layers to deliver the outcome of
    client-side tool execution back to the coordinating service. It contains
    only generic fields and does not expose any internal execution details.
    """

    tool_event_id: str = Field(
        ...,
        description=(
            "Identifier for the tool event that this result corresponds to. "
            "This should match the identifier originally sent in the tool "
            "request event."
        ),
    )
    result: Any = Field(
        ...,
        description="Result value produced by the tool execution.",
    )
