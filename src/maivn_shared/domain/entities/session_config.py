"""Typed session configuration models for SDK and server transport."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .memory_config import MemoryConfig, MemorySharingScope

NestedSynthesisMode = Literal["auto", True, False]
OrchestrationMode = Literal["single_shot_dag", "supervisor_loop", "strict_user_dag", "hybrid"]
FinalOutputMode = Literal["terminal", "supervised", "aggregator_only"]
StopStrategy = Literal[
    "orchestrator_decides",
    "final_tool_completed",
    "objective_satisfied",
    "max_cycles",
    "blocker_detected",
]

_SYSTEM_TOOLS_METADATA_KEYS = {
    "allowed_system_tools",
    "approved_compose_artifact_targets",
    "allow_private_data_in_system_tools",
    "allow_private_data_placeholders_in_system_tools",
}
_EXECUTION_METADATA_KEYS = {
    "agent_id",
    "client_timezone",
    "maivn_sdk_delivery_mode",
    "sdk_deployment_timezone",
    "server_deployment_timezone",
    "timeout",
}
_STRUCTURED_OUTPUT_METADATA_KEYS = {"structured_output_intent", "structured_output_model"}
_ORCHESTRATION_METADATA_KEYS = {
    "allow_followup_actions",
    "allow_reevaluate_loop",
    "final_output_mode",
    "max_orchestration_cycles",
    "orchestration_mode",
    "stop_strategy",
}
_MEMORY_ASSETS_METADATA_KEYS = {
    "memory_defined_skills",
    "memory_bound_resources",
    "memory_recall_turn_active",
}
_SWARM_METADATA_KEYS = {
    "swarm_invocation_intent",
    "swarm_id",
    "swarm_name",
    "swarm_description",
    "swarm_system_prompt",
    "swarm_agent_roster",
    "swarm_agent_invocation_tool_map",
    "swarm_agent_invocation",
    "swarm_use_as_final_output",
    "swarm_invoked_agent_id",
    "swarm_invoked_agent_name",
    "swarm_included_nested_synthesis",
    "maivn_sdk_delivery_mode",
    "swarm_agent_dependency_context",
    "swarm_agent_dependency_context_keys",
}
RESERVED_SESSION_CONFIG_METADATA_KEYS = frozenset(
    _SYSTEM_TOOLS_METADATA_KEYS
    | _EXECUTION_METADATA_KEYS
    | _STRUCTURED_OUTPUT_METADATA_KEYS
    | _ORCHESTRATION_METADATA_KEYS
    | _MEMORY_ASSETS_METADATA_KEYS
    | _SWARM_METADATA_KEYS
)


# MARK: Helpers


def _normalize_optional_text(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    normalized = value.strip()
    return normalized or None


def _normalize_optional_lower_text(value: Any) -> Any:
    normalized = _normalize_optional_text(value)
    if isinstance(normalized, str):
        return normalized.lower()
    return normalized


def _normalize_text_list(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, list):
        return value
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        candidate = item.strip()
        if not candidate or candidate in seen:
            continue
        normalized.append(candidate)
        seen.add(candidate)
    return normalized


def _is_configured_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, list | dict | set | tuple):
        return bool(value)
    return True


def _merge_nested_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _merge_nested_dicts(existing, value)
            continue
        merged[key] = value
    return merged


def is_reserved_session_config_metadata_key(key: str) -> bool:
    """Return True if ``key`` is in the reserved session-config namespace.

    Session-config metadata keys (``orchestration_mode``, ``stop_strategy``,
    etc.) are projected onto the request from the typed config models and
    cannot be overridden via the free-form ``metadata`` dict.
    """
    return key.strip() in RESERVED_SESSION_CONFIG_METADATA_KEYS


# MARK: Execution Config


class SessionExecutionConfig(BaseModel):
    """Typed execution metadata for a session request."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str | None = Field(default=None, description="SDK agent identifier.")
    timeout: int | float | None = Field(default=None, ge=0, description="Execution timeout.")
    sdk_delivery_mode: str | None = Field(
        default=None,
        description="SDK delivery mode used by server-side routing.",
    )
    client_timezone: str | None = Field(
        default=None,
        description="Client IANA timezone used for datetime-aware execution.",
    )
    sdk_deployment_timezone: str | None = Field(
        default=None,
        description="SDK deployment timezone fallback used for datetime-aware execution.",
    )

    @field_validator(
        "agent_id",
        "sdk_delivery_mode",
        "client_timezone",
        "sdk_deployment_timezone",
        mode="before",
    )
    @classmethod
    def _normalize_text_fields(cls, value: Any) -> Any:
        return _normalize_optional_text(value)

    def is_configured(self) -> bool:
        return any(
            value is not None
            for value in (
                self.agent_id,
                self.timeout,
                self.sdk_delivery_mode,
                self.client_timezone,
                self.sdk_deployment_timezone,
            )
        )

    def merged_with(self, override: SessionExecutionConfig | None) -> SessionExecutionConfig:
        if override is None or not override.is_configured():
            return self.model_copy(deep=True)
        merged_payload = _merge_nested_dicts(
            self.model_dump(exclude_none=True),
            override.model_dump(exclude_none=True),
        )
        return type(self).model_validate(merged_payload)

    def to_metadata_patch(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if self.agent_id is not None:
            metadata["agent_id"] = self.agent_id
        if self.timeout is not None:
            metadata["timeout"] = self.timeout
        if self.sdk_delivery_mode is not None:
            metadata["maivn_sdk_delivery_mode"] = self.sdk_delivery_mode
        if self.client_timezone is not None:
            metadata["client_timezone"] = self.client_timezone
        if self.sdk_deployment_timezone is not None:
            metadata["sdk_deployment_timezone"] = self.sdk_deployment_timezone
        return metadata

    @classmethod
    def merge(cls, *configs: SessionExecutionConfig | None) -> SessionExecutionConfig | None:
        merged: SessionExecutionConfig | None = None
        for config in configs:
            if config is None or not config.is_configured():
                continue
            merged = config.model_copy(deep=True) if merged is None else merged.merged_with(config)
        return merged


# MARK: System Tools Config


class SystemToolsConfig(BaseModel):
    """Typed controls for server-side system tool availability and approvals."""

    model_config = ConfigDict(extra="forbid")

    allowed_tools: list[str] | None = Field(
        default=None,
        description="System tool allowlist. Use an empty list to disable all system tools.",
    )
    approved_compose_artifact_targets: list[str] | bool | None = Field(
        default=None,
        description="Explicit compose_artifact target approvals, or True to approve all.",
    )
    allow_private_data: bool | None = Field(
        default=None,
        description="Allow system tools to receive raw private_data values.",
    )
    allow_private_data_placeholders: bool | None = Field(
        default=None,
        description="Allow system tools to receive private-data placeholders.",
    )

    @field_validator("allowed_tools", mode="before")
    @classmethod
    def _normalize_allowed_tools(cls, value: Any) -> Any:
        return _normalize_text_list(value)

    @field_validator("approved_compose_artifact_targets", mode="before")
    @classmethod
    def _normalize_approved_targets(cls, value: Any) -> Any:
        if value is None or isinstance(value, bool):
            return value
        return _normalize_text_list(value)

    def is_configured(self) -> bool:
        return any(
            value is not None
            for value in (
                self.allowed_tools,
                self.approved_compose_artifact_targets,
                self.allow_private_data,
                self.allow_private_data_placeholders,
            )
        )

    def merged_with(self, override: SystemToolsConfig | None) -> SystemToolsConfig:
        if override is None or not override.is_configured():
            return self.model_copy(deep=True)
        merged_payload = _merge_nested_dicts(
            self.model_dump(exclude_none=True),
            override.model_dump(exclude_none=True),
        )
        return type(self).model_validate(merged_payload)

    def to_metadata_patch(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if self.allowed_tools is not None:
            metadata["allowed_system_tools"] = list(self.allowed_tools)
        if self.approved_compose_artifact_targets is not None:
            metadata["approved_compose_artifact_targets"] = (
                list(self.approved_compose_artifact_targets)
                if isinstance(self.approved_compose_artifact_targets, list)
                else self.approved_compose_artifact_targets
            )
        if self.allow_private_data is not None:
            metadata["allow_private_data_in_system_tools"] = self.allow_private_data
        if self.allow_private_data_placeholders is not None:
            metadata["allow_private_data_placeholders_in_system_tools"] = (
                self.allow_private_data_placeholders
            )
        return metadata

    @classmethod
    def merge(cls, *configs: SystemToolsConfig | None) -> SystemToolsConfig | None:
        merged: SystemToolsConfig | None = None
        for config in configs:
            if config is None or not config.is_configured():
                continue
            merged = config.model_copy(deep=True) if merged is None else merged.merged_with(config)
        return merged


# MARK: Structured Output Config


class StructuredOutputConfig(BaseModel):
    """Typed structured-output transport intent."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool | None = Field(default=None)
    model: str | None = Field(default=None, description="Structured output model name.")

    @field_validator("model", mode="before")
    @classmethod
    def _normalize_model(cls, value: Any) -> Any:
        return _normalize_optional_text(value)

    def is_configured(self) -> bool:
        return self.enabled is not None or self.model is not None

    def to_metadata_patch(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if self.enabled is not None:
            metadata["structured_output_intent"] = self.enabled
        if self.model is not None:
            metadata["structured_output_model"] = self.model
        return metadata


# MARK: Orchestration Config


class SessionOrchestrationConfig(BaseModel):
    """Typed orchestration loop controls for a session request."""

    model_config = ConfigDict(extra="forbid")

    mode: OrchestrationMode | None = Field(
        default=None,
        description="How the orchestrator should plan and supervise action batches.",
    )
    final_output_mode: FinalOutputMode | None = Field(
        default=None,
        description="Whether final tools or final-output agents are terminal or supervised.",
    )
    allow_followup_actions: bool | None = Field(
        default=None,
        description="Allow the orchestrator to create additional actions after a batch completes.",
    )
    stop_strategy: StopStrategy | None = Field(
        default=None,
        description="High-level completion strategy used by the orchestrator/runtime.",
    )
    allow_reevaluate_loop: bool | None = Field(
        default=None,
        description="Allow reevaluate to continue after a complete result is available.",
    )
    max_cycles: int | None = Field(
        default=None,
        gt=0,
        description="Maximum orchestration loop cycles for this request.",
    )

    @field_validator("mode", "final_output_mode", "stop_strategy", mode="before")
    @classmethod
    def _normalize_policy_text(cls, value: Any) -> Any:
        return _normalize_optional_lower_text(value)

    def is_configured(self) -> bool:
        return any(
            value is not None
            for value in (
                self.mode,
                self.final_output_mode,
                self.allow_followup_actions,
                self.stop_strategy,
                self.allow_reevaluate_loop,
                self.max_cycles,
            )
        )

    def to_metadata_patch(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if self.mode is not None:
            metadata["orchestration_mode"] = self.mode
        if self.final_output_mode is not None:
            metadata["final_output_mode"] = self.final_output_mode
        if self.allow_followup_actions is not None:
            metadata["allow_followup_actions"] = self.allow_followup_actions
        if self.stop_strategy is not None:
            metadata["stop_strategy"] = self.stop_strategy
        if self.allow_reevaluate_loop is not None:
            metadata["allow_reevaluate_loop"] = self.allow_reevaluate_loop
        if self.max_cycles is not None:
            metadata["max_orchestration_cycles"] = self.max_cycles
        return metadata

    def merged_with(
        self,
        override: SessionOrchestrationConfig | None,
    ) -> SessionOrchestrationConfig:
        if override is None or not override.is_configured():
            return self.model_copy(deep=True)
        merged_payload = _merge_nested_dicts(
            self.model_dump(exclude_none=True),
            override.model_dump(exclude_none=True),
        )
        return type(self).model_validate(merged_payload)

    @classmethod
    def merge(
        cls,
        *configs: SessionOrchestrationConfig | None,
    ) -> SessionOrchestrationConfig | None:
        merged: SessionOrchestrationConfig | None = None
        for config in configs:
            if config is None or not config.is_configured():
                continue
            merged = config.model_copy(deep=True) if merged is None else merged.merged_with(config)
        return merged


# MARK: Memory Assets Config


class MemorySkillConfig(BaseModel):
    """Typed user-defined memory skill payload."""

    model_config = ConfigDict(extra="allow")

    skill_id: str | None = None
    id: str | None = None
    name: str | None = None
    title: str | None = None
    description: str | None = None
    content: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    preconditions: dict[str, Any] = Field(default_factory=dict)
    postconditions: dict[str, Any] = Field(default_factory=dict)
    sharing_scope: MemorySharingScope | None = None
    origin: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    agent_id: str | None = None
    swarm_id: str | None = None

    @field_validator(
        "skill_id",
        "id",
        "name",
        "title",
        "description",
        "content",
        "origin",
        "agent_id",
        "swarm_id",
        mode="before",
    )
    @classmethod
    def _normalize_text_fields(cls, value: Any) -> Any:
        return _normalize_optional_text(value)

    @field_validator("sharing_scope", mode="before")
    @classmethod
    def _normalize_sharing_scope(cls, value: Any) -> Any:
        return _normalize_optional_lower_text(value)

    @model_validator(mode="after")
    def _validate_identity(self) -> MemorySkillConfig:
        if self.name is None and self.title is None:
            raise ValueError("MemorySkillConfig requires name or title")
        return self

    def to_metadata_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class MemoryResourceConfig(BaseModel):
    """Typed bound memory resource payload."""

    model_config = ConfigDict(extra="allow")

    resource_id: str | None = None
    id: str | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    content: str | None = None
    source_url: str | None = None
    url: str | None = None
    content_base64: str | None = None
    mime_type: str | None = None
    tags: list[str] = Field(default_factory=list)
    binding_type: str | None = None
    sharing_scope: MemorySharingScope | None = None
    source_type: str | None = None
    agent_id: str | None = None
    swarm_id: str | None = None

    @field_validator(
        "resource_id",
        "id",
        "title",
        "name",
        "description",
        "content",
        "source_url",
        "url",
        "content_base64",
        "mime_type",
        "binding_type",
        "source_type",
        "agent_id",
        "swarm_id",
        mode="before",
    )
    @classmethod
    def _normalize_text_fields(cls, value: Any) -> Any:
        return _normalize_optional_text(value)

    @field_validator("sharing_scope", mode="before")
    @classmethod
    def _normalize_sharing_scope(cls, value: Any) -> Any:
        return _normalize_optional_lower_text(value)

    @field_validator("tags", mode="before")
    @classmethod
    def _normalize_tags(cls, value: Any) -> Any:
        normalized = _normalize_text_list(value)
        return [] if normalized is None else normalized

    @model_validator(mode="after")
    def _validate_identity(self) -> MemoryResourceConfig:
        if (
            self.title is None
            and self.name is None
            and self.resource_id is None
            and self.id is None
        ):
            raise ValueError("MemoryResourceConfig requires title, name, resource_id, or id")
        return self

    def to_metadata_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class MemoryAssetsConfig(BaseModel):
    """Typed memory assets transported with a session request."""

    model_config = ConfigDict(extra="forbid")

    defined_skills: list[MemorySkillConfig] = Field(default_factory=list)
    bound_resources: list[MemoryResourceConfig] = Field(default_factory=list)
    recall_turn_active: bool | None = None

    def is_configured(self) -> bool:
        return bool(
            self.defined_skills or self.bound_resources or self.recall_turn_active is not None
        )

    def to_metadata_patch(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if self.defined_skills:
            metadata["memory_defined_skills"] = [
                skill.to_metadata_payload() for skill in self.defined_skills
            ]
        if self.bound_resources:
            metadata["memory_bound_resources"] = [
                resource.to_metadata_payload() for resource in self.bound_resources
            ]
        if self.recall_turn_active is not None:
            metadata["memory_recall_turn_active"] = self.recall_turn_active
        return metadata


# MARK: Swarm Config


class SwarmAgentConfig(BaseModel):
    """Typed swarm roster entry for one member agent."""

    model_config = ConfigDict(extra="allow")

    agent_id: str | None = None
    name: str | None = None
    description: str | None = None
    use_as_final_output: bool = False
    included_nested_synthesis: NestedSynthesisMode | None = None
    included_nested_synthesis_guidance: str | None = None
    has_final_tool: bool = False
    invocation_tool_id: str | None = None
    invokes_via_dependency: list[str] = Field(default_factory=list)
    """Names of swarm-member agents this agent will auto-invoke via
    ``@depends_on_agent`` on one of its tools. The orchestrator uses this to
    avoid scheduling a redundant separate stage for an agent that's already
    going to be invoked as a tool dependency."""
    memory_config: MemoryConfig | None = None
    memory_defined_skills: list[MemorySkillConfig] = Field(default_factory=list)
    memory_bound_resources: list[MemoryResourceConfig] = Field(default_factory=list)

    @field_validator(
        "agent_id",
        "name",
        "description",
        "included_nested_synthesis_guidance",
        "invocation_tool_id",
        mode="before",
    )
    @classmethod
    def _normalize_text_fields(cls, value: Any) -> Any:
        return _normalize_optional_text(value)

    @field_validator("included_nested_synthesis", mode="before")
    @classmethod
    def _normalize_nested_synthesis(cls, value: Any) -> Any:
        return normalize_nested_synthesis(value)

    def to_metadata_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class SwarmConfig(BaseModel):
    """Typed swarm orchestration transport config."""

    model_config = ConfigDict(extra="forbid")

    invocation_intent: bool | None = None
    swarm_id: str | None = None
    swarm_name: str | None = None
    swarm_description: str | None = None
    swarm_system_prompt: str | None = None
    agent_roster: list[SwarmAgentConfig] = Field(default_factory=list)
    agent_invocation_tool_map: dict[str, str] = Field(default_factory=dict)
    agent_invocation: bool | None = None
    use_as_final_output: bool | None = None
    invoked_agent_id: str | None = None
    invoked_agent_name: str | None = None
    included_nested_synthesis: NestedSynthesisMode | None = None
    sdk_delivery_mode: str | None = None
    agent_dependency_context: dict[str, Any] | None = None
    agent_dependency_context_keys: list[str] | None = None
    swarm_has_final_tool: bool = False

    @field_validator(
        "swarm_id",
        "swarm_name",
        "swarm_description",
        "swarm_system_prompt",
        "invoked_agent_id",
        "invoked_agent_name",
        "sdk_delivery_mode",
        mode="before",
    )
    @classmethod
    def _normalize_text_fields(cls, value: Any) -> Any:
        return _normalize_optional_text(value)

    @field_validator("included_nested_synthesis", mode="before")
    @classmethod
    def _normalize_nested_synthesis(cls, value: Any) -> Any:
        return normalize_nested_synthesis(value)

    @field_validator("agent_dependency_context_keys", mode="before")
    @classmethod
    def _normalize_dependency_context_keys(cls, value: Any) -> Any:
        return _normalize_text_list(value)

    def is_configured(self) -> bool:
        return any(
            _is_configured_value(value)
            for value in (
                self.invocation_intent,
                self.swarm_id,
                self.swarm_name,
                self.swarm_description,
                self.swarm_system_prompt,
                self.agent_roster,
                self.agent_invocation_tool_map,
                self.agent_invocation,
                self.use_as_final_output,
                self.invoked_agent_id,
                self.invoked_agent_name,
                self.included_nested_synthesis,
                self.sdk_delivery_mode,
                self.agent_dependency_context,
                self.agent_dependency_context_keys,
            )
        )

    def to_metadata_patch(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if self.invocation_intent is not None:
            metadata["swarm_invocation_intent"] = self.invocation_intent
        if self.swarm_id is not None:
            metadata["swarm_id"] = self.swarm_id
        if self.swarm_name is not None:
            metadata["swarm_name"] = self.swarm_name
        if self.swarm_description is not None:
            metadata["swarm_description"] = self.swarm_description
        if self.swarm_system_prompt is not None:
            metadata["swarm_system_prompt"] = self.swarm_system_prompt
        if self.agent_roster:
            metadata["swarm_agent_roster"] = [
                agent.to_metadata_payload() for agent in self.agent_roster
            ]
        if self.agent_invocation_tool_map:
            metadata["swarm_agent_invocation_tool_map"] = dict(self.agent_invocation_tool_map)
        if self.agent_invocation is not None:
            metadata["swarm_agent_invocation"] = self.agent_invocation
        if self.use_as_final_output is not None:
            metadata["swarm_use_as_final_output"] = self.use_as_final_output
        if self.invoked_agent_id is not None:
            metadata["swarm_invoked_agent_id"] = self.invoked_agent_id
        if self.invoked_agent_name is not None:
            metadata["swarm_invoked_agent_name"] = self.invoked_agent_name
        if self.included_nested_synthesis is not None:
            metadata["swarm_included_nested_synthesis"] = self.included_nested_synthesis
        if self.sdk_delivery_mode is not None:
            metadata["maivn_sdk_delivery_mode"] = self.sdk_delivery_mode
        if self.agent_dependency_context is not None:
            metadata["swarm_agent_dependency_context"] = dict(self.agent_dependency_context)
        if self.agent_dependency_context_keys is not None:
            metadata["swarm_agent_dependency_context_keys"] = list(
                self.agent_dependency_context_keys
            )
        if self.swarm_has_final_tool:
            metadata["swarm_has_final_tool"] = True
        return metadata


# MARK: Normalization


def normalize_nested_synthesis(value: Any) -> NestedSynthesisMode | None:
    """Coerce user input into the canonical nested-synthesis mode.

    Accepts ``None``, ``bool``, or string forms (``"auto"``, ``"true"``,
    ``"yes"``, ``"on"``, ``"false"``, etc., case-insensitive). Raises
    ``ValueError`` for any other shape so callers don't silently fall
    through to ``"auto"``.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "auto":
            return "auto"
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    raise ValueError("included_nested_synthesis must be True, False, 'auto', or None")


def apply_session_configs_to_metadata(
    metadata: dict[str, Any],
    *,
    execution_config: SessionExecutionConfig | None = None,
    system_tools_config: SystemToolsConfig | None = None,
    structured_output_config: StructuredOutputConfig | None = None,
    orchestration_config: SessionOrchestrationConfig | None = None,
    memory_assets_config: MemoryAssetsConfig | None = None,
    swarm_config: SwarmConfig | None = None,
) -> None:
    """Project typed session configs into legacy runtime metadata."""
    if execution_config is not None and execution_config.is_configured():
        metadata.update(execution_config.to_metadata_patch())
    if system_tools_config is not None and system_tools_config.is_configured():
        metadata.update(system_tools_config.to_metadata_patch())
    if structured_output_config is not None and structured_output_config.is_configured():
        metadata.update(structured_output_config.to_metadata_patch())
    if orchestration_config is not None and orchestration_config.is_configured():
        metadata.update(orchestration_config.to_metadata_patch())
    if memory_assets_config is not None and memory_assets_config.is_configured():
        metadata.update(memory_assets_config.to_metadata_patch())
    if swarm_config is not None and swarm_config.is_configured():
        metadata.update(swarm_config.to_metadata_patch())


__all__ = [
    "FinalOutputMode",
    "MemoryAssetsConfig",
    "MemoryResourceConfig",
    "MemorySkillConfig",
    "NestedSynthesisMode",
    "OrchestrationMode",
    "RESERVED_SESSION_CONFIG_METADATA_KEYS",
    "SessionExecutionConfig",
    "SessionOrchestrationConfig",
    "StopStrategy",
    "StructuredOutputConfig",
    "SwarmAgentConfig",
    "SwarmConfig",
    "SystemToolsConfig",
    "apply_session_configs_to_metadata",
    "is_reserved_session_config_metadata_key",
    "normalize_nested_synthesis",
]
