# pyright: strict
"""Shared normalization, merge, and configured-value helpers for session configs."""

from __future__ import annotations

from collections.abc import Sized
from typing import ClassVar, Self, TypeAlias, cast

from pydantic import BaseModel, ConfigDict, JsonValue

JsonObject: TypeAlias = dict[str, JsonValue]

_SIZED_TYPES: tuple[type, ...] = (list, dict, set, tuple)


# MARK: Text Normalization


def normalize_optional_text(value: object) -> object:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    normalized = value.strip()
    return normalized or None


def normalize_optional_lower_text(value: object) -> object:
    normalized = normalize_optional_text(value)
    if isinstance(normalized, str):
        return normalized.lower()
    return normalized


def normalize_text_list(value: object) -> object:
    if value is None:
        return None
    if not isinstance(value, list):
        return value
    normalized: list[str] = []
    seen: set[str] = set()
    for item in cast(list[object], value):
        if not isinstance(item, str):
            continue
        candidate = item.strip()
        if not candidate or candidate in seen:
            continue
        normalized.append(candidate)
        seen.add(candidate)
    return normalized


# MARK: Configured-Value Checks


def is_configured_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, _SIZED_TYPES):
        return len(cast(Sized, value)) > 0
    return True


# MARK: Dict Merge


def merge_nested_dicts(base: JsonObject, override: JsonObject) -> JsonObject:
    merged = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = merge_nested_dicts(
                cast(JsonObject, existing),
                cast(JsonObject, value),
            )
            continue
        merged[key] = value
    return merged


# MARK: Metadata-Payload Mixin


class MetadataPayloadConfig(BaseModel):
    """Mixin for memory/swarm models that emit their full dump as metadata payload."""

    def to_metadata_payload(self) -> JsonObject:
        return cast(JsonObject, self.model_dump(mode="json", exclude_none=True))


# MARK: Mergeable Config Base


class MergeableConfig(BaseModel):
    """Base for flat session-config models that support field-level merging.

    Subclasses declare ``_configured_field_names`` to enumerate the fields that
    participate in ``is_configured`` and ``merged_with``. Because these models are
    entirely flat (scalar/``list[str]`` fields, no nested ``BaseModel``), merging
    overlays the override's set, non-``None`` fields onto ``self`` via a plain
    ``model_dump(exclude_none=True)`` dict merge plus a single ``model_validate``.
    This drops the ``mode='json'`` serialization and recursive nested-dict merge
    the round-trip carried, while keeping the fresh, independently-owned result
    the previous round-trip produced (no shared mutable substructure).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    _configured_field_names: ClassVar[tuple[str, ...]] = ()

    def _configured_values(self) -> tuple[object, ...]:
        return tuple(getattr(self, name) for name in self._configured_field_names)

    def is_configured(self) -> bool:
        return any(value is not None for value in self._configured_values())

    def merged_with(self, override: Self | None) -> Self:
        if override is None or not override.is_configured():
            return self.model_copy(deep=True)
        merged = {
            **self.model_dump(exclude_none=True),
            **override.model_dump(exclude_none=True),
        }
        return type(self).model_validate(merged)

    @classmethod
    def merge(cls, *configs: Self | None) -> Self | None:
        merged: Self | None = None
        for config in configs:
            if config is None or not config.is_configured():
                continue
            merged = config.model_copy(deep=True) if merged is None else merged.merged_with(config)
        return merged


__all__ = [
    "JsonObject",
    "MergeableConfig",
    "MetadataPayloadConfig",
    "is_configured_value",
    "merge_nested_dicts",
    "normalize_optional_lower_text",
    "normalize_optional_text",
    "normalize_text_list",
]
