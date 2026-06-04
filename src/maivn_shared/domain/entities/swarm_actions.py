"""Swarm action plan models shared across services."""

# pyright: strict
from __future__ import annotations

from typing import ClassVar, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

# MARK: Base Actions


class SwarmActionBase(BaseModel):
    """Base fields shared by all swarm actions."""

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True, extra="ignore")

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


# MARK: Concrete Actions


class AssignmentAgentAction(SwarmActionBase):
    """Action that runs the assignment_agent."""

    goal: str | dict[str, JsonValue] | None = None
    prompt: str | dict[str, JsonValue] | None = None
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
    prompt: str | dict[str, JsonValue] | None = None
    goal: str | dict[str, JsonValue] | None = None
    targeted_tools: list[str] | None = None
    force_final_tool: bool = False

    @model_validator(mode="after")
    def _validate_agent_id(self) -> SwarmAgentAction:
        if not isinstance(self.agent_id, str) or not self.agent_id.strip():
            raise ValueError("swarm_agent actions require agent_id")
        return self


SwarmAction = AssignmentAgentAction | SwarmAgentAction


# MARK: Action Plan


def _empty_swarm_actions() -> list[SwarmAction]:
    return []


class SwarmActionPlan(BaseModel):
    """Structured swarm action plan returned by orchestrator_agent."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    actions: list[SwarmAction] = Field(default_factory=_empty_swarm_actions)

    @model_validator(mode="after")
    def _validate_action_plan(self) -> SwarmActionPlan:
        if not self.actions:
            raise ValueError("SwarmActionPlan requires at least one action")

        final_count = sum(1 for action in self.actions if action.use_as_final_output)
        if final_count > 1:
            raise ValueError("Only one action may have use_as_final_output=True")

        action_ids = [a.action_id for a in self.actions if a.action_id]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("action_id values must be unique when provided")

        action_id_set = set(action_ids)
        for action in self.actions:
            for dependency_id in action.depends_on:
                if action.action_id == dependency_id:
                    raise ValueError(f"action_id {dependency_id!r} cannot depend on itself")
                if dependency_id not in action_id_set:
                    raise ValueError(f"depends_on references unknown action_id {dependency_id!r}")

        self._validate_acyclic_dependencies(action_ids)
        return self

    def _validate_acyclic_dependencies(self, action_ids: list[str]) -> None:
        action_id_set = set(action_ids)
        dependencies_by_id: dict[str, list[str]] = {}
        for action in self.actions:
            action_id = action.action_id
            if action_id is not None and action_id in action_id_set:
                dependencies_by_id[action_id] = list(action.depends_on)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(action_id: str) -> None:
            if action_id in visited:
                return
            if action_id in visiting:
                raise ValueError(f"depends_on cycle detected involving action_id {action_id!r}")

            visiting.add(action_id)
            for dependency_id in dependencies_by_id.get(action_id, []):
                visit(dependency_id)
            visiting.remove(action_id)
            visited.add(action_id)

        for action_id in action_ids:
            visit(action_id)


# MARK: Public API

__all__ = [
    "SwarmActionBase",
    "AssignmentAgentAction",
    "SwarmAgentAction",
    "SwarmAction",
    "SwarmActionPlan",
]
