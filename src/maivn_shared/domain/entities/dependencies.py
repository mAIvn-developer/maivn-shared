"""Tool dependency models for maivn-core.

This module defines dependency models that specify how tools can depend on
other tools, agents, data, or user input. These dependencies are resolved
at execution time by the orchestration layer.

Dependency types:
- AgentDependency: Depends on another agent's output
- ToolDependency: Depends on another tool's output
- DataDependency: Depends on user-provided data
- InterruptDependency: Requires user input at runtime (interrupts execution)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# MARK: - Type Aliases

DependencyType = Literal["agent", "tool", "data", "user", "await_for", "reevaluate"]
InputType = Literal["text", "choice", "boolean", "number", "email", "password", "literal"]
ExecutionTiming = Literal["before", "after"]
ExecutionInstanceControl = Literal["each", "all"]

# MARK: - Base Model


class BaseDependency(BaseModel):
    """Base model for tool dependencies in maivn-core package."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(default="", description="Name of the dependency")
    dependency_type: DependencyType = Field(..., description="Type of dependency")
    arg_name: str = Field(..., description="Argument name for the dependency")


# MARK: - Concrete Dependencies


class AgentDependency(BaseDependency):
    """Dependency on another agent's output."""

    dependency_type: DependencyType = Field(default="agent", description="Type of dependency")
    agent_id: str = Field(..., description="ID of the dependent agent")


class ToolDependency(BaseDependency):
    """Dependency on another tool's output."""

    dependency_type: DependencyType = Field(default="tool", description="Type of dependency")
    tool_id: str = Field(..., description="ID or name of the dependent tool")


class DataDependency(BaseDependency):
    """Dependency on user-provided data from scope."""

    dependency_type: DependencyType = Field(default="data", description="Type of dependency")
    data_key: str = Field(..., description="Key to look up on the scope private_data")


class InterruptDependency(BaseDependency):
    """Dependency requiring user input that interrupts execution."""

    dependency_type: DependencyType = Field(default="user", description="Type of dependency")
    prompt: str = Field(default="", description="Prompt to display when requesting input")
    input_handler: Callable[[str], Any] = Field(
        ..., description="Callable that accepts prompt and returns input value"
    )
    input_type: InputType = Field(
        default="text",
        description="Type of input: text, choice, boolean, number, email, password, literal",
    )
    choices: list[str] = Field(
        default_factory=list,
        description="Available choices for choice/literal input types",
    )

    @model_validator(mode="after")
    def _validate_choices_after_model_creation(self) -> InterruptDependency:
        if self.input_type in {"choice", "literal"} and not self.choices:
            raise ValueError("choices must be provided when input_type is 'choice' or 'literal'")
        return self


class AwaitForDependency(BaseDependency):
    """Execution-control dependency for sequencing without data transfer."""

    dependency_type: DependencyType = Field(default="await_for", description="Type of dependency")
    arg_name: str = Field(default="", description="Unused for metadata-only execution controls")
    tool_id: str = Field(..., description="ID or name of the target tool")
    tool_name: str = Field(default="", description="Human-readable target tool name")
    timing: ExecutionTiming = Field(default="after", description="Relative sequencing direction")
    instance_control: ExecutionInstanceControl = Field(
        default="each",
        description="Whether sequencing applies pairwise or across all matching instances",
    )


class ReevaluateDependency(BaseDependency):
    """Execution-control dependency for reevaluate placement around tool instances."""

    dependency_type: DependencyType = Field(default="reevaluate", description="Type of dependency")
    arg_name: str = Field(default="", description="Unused for metadata-only execution controls")
    tool_id: str = Field(..., description="ID or name of the target tool")
    tool_name: str = Field(default="", description="Human-readable target tool name")
    timing: ExecutionTiming = Field(default="after", description="Relative reevaluate timing")
    instance_control: ExecutionInstanceControl = Field(
        default="each",
        description="Whether reevaluate applies per instance or across all matching instances",
    )
