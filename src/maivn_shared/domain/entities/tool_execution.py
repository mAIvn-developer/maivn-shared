"""Tool execution models for SDK interface."""

# pyright: strict
from __future__ import annotations

from pydantic import BaseModel, Field, JsonValue

# MARK: Tool Execution Entities


class ToolCall(BaseModel):
    """Details about a single tool invocation request."""

    tool_id: str = Field(..., description="Identifier for the tool to execute")
    args: dict[str, JsonValue] = Field(
        default_factory=dict,
        description="Arguments provided for the tool execution",
    )


class ToolExecutionResult(BaseModel):
    """Result of a tool execution."""

    value: str = Field(..., description="Serialized result payload")
