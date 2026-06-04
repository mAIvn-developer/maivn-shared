# pyright: strict
from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import is_dataclass
from typing import cast

from pydantic import JsonValue

from ...entities.tool_spec import ToolSpec, ToolType
from .docstring_utils import extract_function_description, parse_docstring_args
from .schema_utils import (
    JsonSchema,
    build_dataclass_schema,
    build_object_schema,
    build_property_schema,
    type_hints,
)

# MARK: - Public API


def build_tool_spec_from_function(
    func: Callable[..., object],
    *,
    tool_id: str,
    agent_id: str = "system_agents",
    name: str | None = None,
    tool_type: ToolType = "agent",
    metadata: dict[str, object] | None = None,
    always_execute: bool = False,
    final_tool: bool = False,
) -> ToolSpec:
    """Build a ToolSpec dynamically from an async function."""
    tool_name = name or func.__name__
    description = extract_function_description(func)

    args_schema = _build_args_schema_from_function(func)
    resolved_metadata = _build_metadata(func, metadata)

    return ToolSpec(
        tool_id=tool_id,
        agent_id=agent_id,
        name=tool_name,
        description=description,
        tool_type=tool_type,
        args_schema=args_schema,
        always_execute=always_execute,
        final_tool=final_tool,
        metadata=cast(JsonSchema, resolved_metadata),
    )


# MARK: - Schema Building


def _build_args_schema_from_function(func: Callable[..., object]) -> JsonSchema:
    """Build args schema from function signature and type hints."""
    hints = type_hints(func)
    sig = inspect.signature(func)
    param_docs = parse_docstring_args(func.__doc__ or "")

    properties: dict[str, JsonValue] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        param_type = hints.get(param_name, object)
        param_description = param_docs.get(param_name, "")

        properties[param_name] = build_property_schema(param_type, param_description)

        default_value = cast(object, param.default)
        if default_value is inspect.Parameter.empty:
            required.append(param_name)

    schema = build_object_schema(properties)
    schema["required"] = cast(JsonValue, required)
    return schema


def _build_return_type_schema_from_annotation(return_type: object) -> JsonSchema:
    """Build a return-type schema from a function's return annotation."""
    if is_dataclass(return_type) and isinstance(return_type, type):
        return build_dataclass_schema(return_type)

    return build_property_schema(return_type, "")


# MARK: - Metadata Building


def _build_metadata(
    func: Callable[..., object],
    metadata: dict[str, object] | None,
) -> dict[str, object]:
    """Build metadata dict with return type schema if applicable."""
    hints = type_hints(func)
    return_type = hints.get("return")

    resolved_metadata: dict[str, object] = metadata.copy() if metadata else {}
    resolved_metadata["type"] = "SYSTEM"

    if return_type is not None:
        resolved_metadata["return_type"] = _build_return_type_schema_from_annotation(return_type)

    return resolved_metadata
