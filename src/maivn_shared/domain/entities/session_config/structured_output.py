# pyright: strict
"""Typed structured-output transport intent."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._helpers import JsonObject, normalize_optional_text

# MARK: Structured Output Config


class StructuredOutputConfig(BaseModel):
    """Typed structured-output transport intent."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    enabled: bool | None = Field(default=None)
    model: str | None = Field(default=None, description="Structured output model name.")

    @field_validator("model", mode="before")
    @classmethod
    def _normalize_model(cls, value: object) -> object:
        return normalize_optional_text(value)

    def is_configured(self) -> bool:
        return self.enabled is not None or self.model is not None

    def to_metadata_patch(self) -> JsonObject:
        metadata: JsonObject = {}
        if self.enabled is not None:
            metadata["structured_output_intent"] = self.enabled
        if self.model is not None:
            metadata["structured_output_model"] = self.model
        return metadata


__all__ = ["StructuredOutputConfig"]
