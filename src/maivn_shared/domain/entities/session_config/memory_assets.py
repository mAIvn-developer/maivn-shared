# pyright: strict
"""Typed memory assets (skills, resources) transported with a session request."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..memory_config import MemorySharingScope
from ._helpers import (
    JsonObject,
    MetadataPayloadConfig,
    normalize_optional_lower_text,
    normalize_optional_text,
    normalize_text_list,
)

# MARK: Memory Skill Config


def _empty_json_objects() -> list[JsonObject]:
    return []


def _empty_memory_skills() -> list[MemorySkillConfig]:
    return []


def _empty_memory_resources() -> list[MemoryResourceConfig]:
    return []


class MemorySkillConfig(MetadataPayloadConfig):
    """Typed user-defined memory skill payload."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    skill_id: str | None = None
    id: str | None = None
    name: str | None = None
    title: str | None = None
    description: str | None = None
    content: str | None = None
    steps: list[JsonObject] = Field(default_factory=_empty_json_objects)
    preconditions: JsonObject = Field(default_factory=dict)
    postconditions: JsonObject = Field(default_factory=dict)
    sharing_scope: MemorySharingScope | None = None
    origin: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: JsonObject = Field(default_factory=dict)
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
    def _normalize_text_fields(cls, value: object) -> object:
        return normalize_optional_text(value)

    @field_validator("sharing_scope", mode="before")
    @classmethod
    def _normalize_sharing_scope(cls, value: object) -> object:
        return normalize_optional_lower_text(value)

    @model_validator(mode="after")
    def _validate_identity(self) -> MemorySkillConfig:
        if self.name is None and self.title is None:
            raise ValueError("MemorySkillConfig requires name or title")
        return self


# MARK: Memory Resource Config


class MemoryResourceConfig(MetadataPayloadConfig):
    """Typed bound memory resource payload."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

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
    def _normalize_text_fields(cls, value: object) -> object:
        return normalize_optional_text(value)

    @field_validator("sharing_scope", mode="before")
    @classmethod
    def _normalize_sharing_scope(cls, value: object) -> object:
        return normalize_optional_lower_text(value)

    @field_validator("tags", mode="before")
    @classmethod
    def _normalize_tags(cls, value: object) -> object:
        normalized = normalize_text_list(value)
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


# MARK: Memory Assets Config


class MemoryAssetsConfig(BaseModel):
    """Typed memory assets transported with a session request."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    defined_skills: list[MemorySkillConfig] = Field(default_factory=_empty_memory_skills)
    bound_resources: list[MemoryResourceConfig] = Field(default_factory=_empty_memory_resources)
    recall_turn_active: bool | None = None

    def is_configured(self) -> bool:
        return bool(
            self.defined_skills or self.bound_resources or self.recall_turn_active is not None
        )

    def to_metadata_patch(self) -> JsonObject:
        metadata: JsonObject = {}
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


__all__ = [
    "MemoryAssetsConfig",
    "MemoryResourceConfig",
    "MemorySkillConfig",
]
