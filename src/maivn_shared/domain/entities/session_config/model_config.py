# pyright: strict
"""Scoped model selection configuration for session requests."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

# MARK: Types

ModelTier = Literal["auto", "fast", "balanced", "max"]
ModelConfigPart = Literal["response", "thinking", "compose_artifact", "repl"]
_MODEL_TIERS: frozenset[str] = frozenset(("auto", "fast", "balanced", "max"))


# MARK: Model Choice


class ModelChoice(BaseModel):
    """A single scoped model choice: either a tier or an exact model id."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    tier: ModelTier | None = Field(
        default=None,
        description="Model tier for the scoped framework part.",
    )
    model_id: str | None = Field(
        default=None,
        description="Exact model id for the scoped framework part.",
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_string_choice(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError("Model choice strings must not be empty")
            if stripped in _MODEL_TIERS:
                return {"tier": stripped}
            return {"model_id": stripped}
        return value

    @field_validator("model_id")
    @classmethod
    def _normalize_model_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("model_id must not be empty")
        return stripped

    @model_validator(mode="after")
    def _validate_exactly_one_choice(self) -> ModelChoice:
        has_tier = self.tier is not None
        has_model_id = self.model_id is not None
        if has_tier == has_model_id:
            raise ValueError("Exactly one of tier or model_id must be set")
        return self


# MARK: Model Config


class ModelConfig(BaseModel):
    """Scoped model choices for configurable mAIvn framework parts."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", populate_by_name=True)

    response: ModelChoice | None = Field(
        default=None,
        description="Model choice for final/direct response generation.",
    )
    thinking: ModelChoice | None = Field(
        default=None,
        validation_alias=AliasChoices("thinking", "think"),
        description="Model choice for the think system tool.",
    )
    compose_artifact: ModelChoice | None = Field(
        default=None,
        description="Model choice for compose_artifact system-tool generation.",
    )
    repl: ModelChoice | None = Field(
        default=None,
        description="Model choice for REPL system-tool code generation and repair.",
    )

    @field_validator("response", "thinking", "compose_artifact", "repl", mode="before")
    @classmethod
    def _coerce_choice(cls, value: object) -> object:
        if value is None or isinstance(value, ModelChoice):
            return value
        return ModelChoice.model_validate(value)

    @classmethod
    def for_all(
        cls,
        choice: ModelChoice | str | None = None,
        *,
        tier: ModelTier | None = None,
        model_id: str | None = None,
    ) -> ModelConfig:
        """Build a config that applies the same choice to all configurable parts."""
        if model_id is not None and not model_id.strip():
            raise ValueError("model_id must be a non-empty string")

        explicit_count = int(choice is not None) + int(tier is not None) + int(model_id is not None)
        if explicit_count != 1:
            raise ValueError("Provide exactly one of choice, tier, or model_id")

        raw_choice: ModelChoice | str | dict[str, str]
        if choice is not None:
            raw_choice = choice
        elif tier is not None:
            raw_choice = {"tier": tier}
        else:
            assert model_id is not None
            raw_choice = {"model_id": model_id.strip()}

        resolved = ModelChoice.model_validate(raw_choice)
        return cls(
            response=resolved.model_copy(),
            thinking=resolved.model_copy(),
            compose_artifact=resolved.model_copy(),
            repl=resolved.model_copy(),
        )

    def selection_for(self, part: ModelConfigPart) -> ModelChoice | None:
        """Return the configured choice for a framework part."""
        if part == "response":
            return self.response
        if part == "thinking":
            return self.thinking
        if part == "compose_artifact":
            return self.compose_artifact
        return self.repl

    def model_ids(self) -> list[str]:
        """Return exact model ids referenced by this config, in field order."""
        ids: list[str] = []
        parts: tuple[ModelConfigPart, ...] = ("response", "thinking", "compose_artifact", "repl")
        for part in parts:
            choice = self.selection_for(part)
            if choice is not None and choice.model_id is not None:
                ids.append(choice.model_id)
        return ids


__all__ = ["ModelChoice", "ModelConfig", "ModelConfigPart", "ModelTier"]
