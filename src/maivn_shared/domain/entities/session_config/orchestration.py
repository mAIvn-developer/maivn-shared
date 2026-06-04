# pyright: strict
"""Typed orchestration loop controls for a session request."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field, field_validator

from ._helpers import JsonObject, MergeableConfig, normalize_optional_lower_text

# MARK: Types

OrchestrationMode = Literal["single_shot_dag", "supervisor_loop", "strict_user_dag", "hybrid"]
FinalOutputMode = Literal["terminal", "supervised", "aggregator_only"]
StopStrategy = Literal[
    "orchestrator_decides",
    "final_tool_completed",
    "objective_satisfied",
    "max_cycles",
    "blocker_detected",
]


# MARK: Orchestration Config


class SessionOrchestrationConfig(MergeableConfig):
    """Typed orchestration loop controls for a session request."""

    _configured_field_names: ClassVar[tuple[str, ...]] = (
        "mode",
        "final_output_mode",
        "allow_followup_actions",
        "stop_strategy",
        "allow_reevaluate_loop",
        "max_cycles",
    )

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
    def _normalize_policy_text(cls, value: object) -> object:
        return normalize_optional_lower_text(value)

    def to_metadata_patch(self) -> JsonObject:
        metadata: JsonObject = {}
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


__all__ = [
    "FinalOutputMode",
    "OrchestrationMode",
    "SessionOrchestrationConfig",
    "StopStrategy",
]
