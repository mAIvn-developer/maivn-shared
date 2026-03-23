"""Swarm action plan models shared across services."""

from __future__ import annotations

from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SwarmActionBase(BaseModel):
    """Base fields shared by all swarm actions."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    action_id: str | None = Field(default=None, alias="id")
    action_type: Final[Literal["assignment_agent", "swarm_agent"]]
    name: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    use_as_final_output: bool = False
    timeout_seconds: int | None = None

    @model_validator(mode="after")
    def _validate_action_id(self) -> SwarmActionBase:
        if self.action_id is not None and not self.action_id.strip():
            raise ValueError("action_id must be a non-empty string when provided")
        return self


class AssignmentAgentAction(SwarmActionBase):
    """Action that runs the assignment_agent."""

    goal: str | dict[str, Any] | None = None
    prompt: str | dict[str, Any] | None = None
    capability_hints: list[str] | None = None
    targeted_tools: list[str] | None = None
    force_final_tool: bool = False

    @model_validator(mode="after")
    def _validate_goal_or_prompt(self) -> AssignmentAgentAction:
        goal = self.goal
        prompt = self.prompt
        if goal is None and prompt is None:
            raise ValueError("assignment_agent actions require goal or prompt")
        if self.use_as_final_output:
            raise ValueError("assignment_agent actions cannot set use_as_final_output")
        return self


class SwarmAgentAction(SwarmActionBase):
    """Action that runs a swarm member agent."""

    agent_id: str | None = None
    instance_key: str | None = None
    prompt: str | dict[str, Any] | None = None
    goal: str | dict[str, Any] | None = None
    targeted_tools: list[str] | None = None
    force_final_tool: bool = False

    @model_validator(mode="after")
    def _validate_agent_id(self) -> SwarmAgentAction:
        if not isinstance(self.agent_id, str) or not self.agent_id.strip():
            raise ValueError("swarm_agent actions require agent_id")
        return self


SwarmAction = AssignmentAgentAction | SwarmAgentAction


class SwarmActionPlan(BaseModel):
    """Structured swarm action plan returned by orchestrator_agent."""

    model_config = ConfigDict(extra="ignore")

    actions: list[SwarmAction] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_action_plan(self) -> SwarmActionPlan:
        if not self.actions:
            raise ValueError("actions is required when route='execute_actions'")

        final_count = sum(1 for action in self.actions if bool(action.use_as_final_output))
        if final_count > 1:
            raise ValueError("Only one action may have use_as_final_output=True")

        action_ids = [a.action_id for a in self.actions if a.action_id]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("action_id values must be unique when provided")

        return self


__all__ = [
    "SwarmActionBase",
    "AssignmentAgentAction",
    "SwarmAgentAction",
    "SwarmAction",
    "SwarmActionPlan",
]
