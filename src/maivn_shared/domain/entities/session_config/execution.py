# pyright: strict
"""Typed execution metadata for a session request."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field, field_validator

from ._helpers import JsonObject, MergeableConfig, normalize_optional_text

# MARK: Execution Config


class SessionExecutionConfig(MergeableConfig):
    """Typed execution metadata for a session request."""

    _configured_field_names: ClassVar[tuple[str, ...]] = (
        "agent_id",
        "timeout",
        "sdk_delivery_mode",
        "client_timezone",
        "sdk_deployment_timezone",
    )

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
    def _normalize_text_fields(cls, value: object) -> object:
        return normalize_optional_text(value)

    def to_metadata_patch(self) -> JsonObject:
        metadata: JsonObject = {}
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


__all__ = ["SessionExecutionConfig"]
