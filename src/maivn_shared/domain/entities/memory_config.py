"""Typed public memory configuration models shared across clients and services."""

# pyright: strict
from __future__ import annotations

from typing import ClassVar, Literal, TypeAlias, cast

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator

JsonObject: TypeAlias = dict[str, JsonValue]

MemoryLevel = Literal["none", "glimpse", "focus", "clarity"]
MemoryPersistenceMode = Literal["persist_none", "vector_only", "vector_plus_graph"]
MemorySharingScope = Literal["agent", "swarm", "project", "org"]

_ALLOWED_INTERNAL_MEMORY_METADATA_KEYS = frozenset(
    {
        "memory_bound_resources",
        "memory_defined_skills",
        "memory_recall_turn_active",
    }
)
_EXPLICIT_RESERVED_MEMORY_METADATA_KEYS = frozenset(
    {
        "agent_memory_level",
        "insight_sharing_scope",
        "memory_policy_ceiling",
        "organization_memory_policy",
        "organization_memory_policy_ceiling",
        "organization_settings",
        "organization_tier",
        "skill_sharing_scope",
        "subscription_tier",
        "swarm_agent_memory_level",
        "swarm_memory_level",
    }
)


# MARK: - Helpers


def _normalize_optional_text(value: object) -> object | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    normalized = value.strip().lower()
    return normalized or None


def _merge_nested_dicts(base: JsonObject, override: JsonObject) -> JsonObject:
    merged: JsonObject = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _merge_nested_dicts(
                cast(JsonObject, existing),
                cast(JsonObject, value),
            )
            continue
        merged[key] = value
    return merged


def is_reserved_memory_metadata_key(key: str) -> bool:
    """Return True if ``key`` is reserved for server-managed memory metadata.

    Any ``memory_*`` prefix is reserved by default (apart from an allowlisted
    set used by internal code); a small explicit list covers names that don't
    start with the prefix. User-supplied metadata that collides with reserved
    keys is rejected at validation time to prevent silent overrides.
    """
    normalized = key.strip()
    if not normalized:
        return False
    if normalized in _ALLOWED_INTERNAL_MEMORY_METADATA_KEYS:
        return False
    if normalized.startswith("memory_"):
        return True
    return normalized in _EXPLICIT_RESERVED_MEMORY_METADATA_KEYS


# MARK: - Nested Config


class MemoryRetrievalConfig(BaseModel):
    """Public retrieval controls for memory bootstrap and recall."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", populate_by_name=True)

    top_k: int | None = Field(default=None, ge=1)
    candidate_limit: int | None = Field(default=None, ge=1)
    skills_enabled: bool | None = None
    insights_enabled: bool | None = None
    resources_enabled: bool | None = None
    skill_injection_max_count: int | None = Field(default=None, ge=1)
    insight_injection_max_count: int | None = Field(default=None, ge=1)
    resource_injection_max_count: int | None = Field(default=None, ge=1)
    insight_relevance_floor: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _validate_candidate_limit(self) -> MemoryRetrievalConfig:
        if (
            self.top_k is not None
            and self.candidate_limit is not None
            and self.candidate_limit < self.top_k
        ):
            raise ValueError("candidate_limit must be greater than or equal to top_k")
        return self


class MemorySkillExtractionConfig(BaseModel):
    """Public skill-extraction controls."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    enabled: bool | None = None
    sharing_scope: MemorySharingScope | None = None
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    max_count: int | None = Field(default=None, ge=1)

    @field_validator("sharing_scope", mode="before")
    @classmethod
    def _normalize_sharing_scope(cls, value: object) -> object | None:
        return _normalize_optional_text(value)


class MemoryInsightExtractionConfig(BaseModel):
    """Public insight-extraction controls."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    enabled: bool | None = None
    sharing_scope: Literal["agent", "swarm"] | None = None
    max_count: int | None = Field(default=None, ge=1)
    min_relevance_score: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("sharing_scope", mode="before")
    @classmethod
    def _normalize_sharing_scope(cls, value: object) -> object | None:
        return _normalize_optional_text(value)


# MARK: - Top-Level Config


class MemoryConfig(BaseModel):
    """Public memory configuration for SDK invocations and scope defaults."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    enabled: bool | None = None
    level: MemoryLevel | None = None
    summarization_enabled: bool | None = None
    persistence_mode: MemoryPersistenceMode | None = None
    retrieval: MemoryRetrievalConfig | None = None
    skill_extraction: MemorySkillExtractionConfig | None = None
    insight_extraction: MemoryInsightExtractionConfig | None = None

    @field_validator("level", "persistence_mode", mode="before")
    @classmethod
    def _normalize_literal_fields(cls, value: object) -> object | None:
        return _normalize_optional_text(value)

    def is_configured(self) -> bool:
        return bool(self.model_dump(exclude_none=True))

    def merged_with(self, override: MemoryConfig | None) -> MemoryConfig:
        if override is None or not override.is_configured():
            return self.model_copy(deep=True)
        merged_payload = _merge_nested_dicts(
            cast(JsonObject, self.model_dump(exclude_none=True)),
            cast(JsonObject, override.model_dump(exclude_none=True)),
        )
        return type(self).model_validate(merged_payload)

    @classmethod
    def merge(cls, *configs: MemoryConfig | None) -> MemoryConfig | None:
        merged: MemoryConfig | None = None
        for config in configs:
            if config is None or not config.is_configured():
                continue
            merged = config.model_copy(deep=True) if merged is None else merged.merged_with(config)
        return merged


__all__ = [
    "MemoryConfig",
    "MemoryInsightExtractionConfig",
    "MemoryLevel",
    "MemoryPersistenceMode",
    "MemoryRetrievalConfig",
    "MemorySharingScope",
    "MemorySkillExtractionConfig",
    "is_reserved_memory_metadata_key",
]
