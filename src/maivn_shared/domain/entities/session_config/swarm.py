# pyright: strict
"""Typed swarm orchestration transport config."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..memory_config import MemoryConfig
from ._helpers import (
    JsonObject,
    MetadataPayloadConfig,
    is_configured_value,
    normalize_optional_text,
    normalize_text_list,
)
from .memory_assets import MemoryResourceConfig, MemorySkillConfig

# MARK: Types

NestedSynthesisMode = Literal["auto", True, False]


# MARK: Normalization


def _empty_memory_skills() -> list[MemorySkillConfig]:
    return []


def _empty_memory_resources() -> list[MemoryResourceConfig]:
    return []


def _empty_agent_roster() -> list[SwarmAgentConfig]:
    return []


def normalize_nested_synthesis(value: object) -> NestedSynthesisMode | None:
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


# MARK: Swarm Agent Config


class SwarmAgentConfig(MetadataPayloadConfig):
    """Typed swarm roster entry for one member agent."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

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
    memory_defined_skills: list[MemorySkillConfig] = Field(default_factory=_empty_memory_skills)
    memory_bound_resources: list[MemoryResourceConfig] = Field(
        default_factory=_empty_memory_resources
    )

    @field_validator(
        "agent_id",
        "name",
        "description",
        "included_nested_synthesis_guidance",
        "invocation_tool_id",
        mode="before",
    )
    @classmethod
    def _normalize_text_fields(cls, value: object) -> object:
        return normalize_optional_text(value)

    @field_validator("included_nested_synthesis", mode="before")
    @classmethod
    def _normalize_nested_synthesis(cls, value: object) -> NestedSynthesisMode | None:
        return normalize_nested_synthesis(value)


# MARK: Swarm Config


class SwarmConfig(BaseModel):
    """Typed swarm orchestration transport config."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    invocation_intent: bool | None = None
    swarm_id: str | None = None
    swarm_name: str | None = None
    swarm_description: str | None = None
    swarm_system_prompt: str | None = None
    agent_roster: list[SwarmAgentConfig] = Field(default_factory=_empty_agent_roster)
    agent_invocation_tool_map: dict[str, str] = Field(default_factory=dict)
    agent_invocation: bool | None = None
    use_as_final_output: bool | None = None
    invoked_agent_id: str | None = None
    invoked_agent_name: str | None = None
    included_nested_synthesis: NestedSynthesisMode | None = None
    sdk_delivery_mode: str | None = None
    agent_dependency_context: JsonObject | None = None
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
    def _normalize_text_fields(cls, value: object) -> object:
        return normalize_optional_text(value)

    @field_validator("included_nested_synthesis", mode="before")
    @classmethod
    def _normalize_nested_synthesis(cls, value: object) -> NestedSynthesisMode | None:
        return normalize_nested_synthesis(value)

    @field_validator("agent_dependency_context_keys", mode="before")
    @classmethod
    def _normalize_dependency_context_keys(cls, value: object) -> object:
        return normalize_text_list(value)

    def is_configured(self) -> bool:
        return any(
            is_configured_value(value)
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

    def to_metadata_patch(self) -> JsonObject:
        metadata: JsonObject = {}
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


__all__ = [
    "NestedSynthesisMode",
    "SwarmAgentConfig",
    "SwarmConfig",
    "normalize_nested_synthesis",
]
