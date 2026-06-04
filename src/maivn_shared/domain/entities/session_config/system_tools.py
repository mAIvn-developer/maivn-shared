# pyright: strict
"""Typed controls for server-side system tool availability and approvals."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field, field_validator

from ._helpers import JsonObject, MergeableConfig, normalize_text_list

# MARK: System Tools Config


class SystemToolsConfig(MergeableConfig):
    """Typed controls for server-side system tool availability and approvals."""

    _configured_field_names: ClassVar[tuple[str, ...]] = (
        "allowed_tools",
        "approved_compose_artifact_targets",
        "allow_private_data",
        "allow_private_data_placeholders",
    )

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
    def _normalize_allowed_tools(cls, value: object) -> object:
        return normalize_text_list(value)

    @field_validator("approved_compose_artifact_targets", mode="before")
    @classmethod
    def _normalize_approved_targets(cls, value: object) -> object:
        if value is None or isinstance(value, bool):
            return value
        return normalize_text_list(value)

    def to_metadata_patch(self) -> JsonObject:
        metadata: JsonObject = {}
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


__all__ = ["SystemToolsConfig"]
