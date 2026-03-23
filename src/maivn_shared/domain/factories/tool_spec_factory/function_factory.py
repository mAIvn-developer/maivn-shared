from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import is_dataclass
from typing import Any, get_type_hints

from maivn_shared.domain.entities.tool_spec import ToolSpec, ToolType

from .docstring_utils import _extract_function_description, _parse_docstring_args
from .schema_utils import _build_dataclass_schema, _build_property_schema

# MARK: - Public API


def build_tool_spec_from_function(
    func: Callable[..., Any],
    *,
    tool_id: str,
    agent_id: str = "system_agents",
    name: str | None = None,
    tool_type: ToolType = "agent",
    metadata: dict[str, Any] | None = None,
    always_execute: bool = False,
    final_tool: bool = False,
) -> ToolSpec:
    """Build a ToolSpec dynamically from an async function."""
    tool_name = name or func.__name__
    description = _extract_function_description(func)

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
        metadata=resolved_metadata,
    )


# MARK: - Schema Building


def _build_args_schema_from_function(func: Callable[..., Any]) -> dict[str, Any]:
    """Build args schema from function signature and type hints."""
    hints = get_type_hints(func, include_extras=True)
    sig = inspect.signature(func)
    param_docs = _parse_docstring_args(func.__doc__ or "")

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        param_type = hints.get(param_name, Any)
        param_description = param_docs.get(param_name, "")

        properties[param_name] = _build_property_schema(param_type, param_description)

        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _build_return_schema_from_type(return_type: Any) -> dict[str, Any]:
    """Build a return schema from a return type annotation."""
    if is_dataclass(return_type) and isinstance(return_type, type):
        return _build_dataclass_schema(return_type)

    return _build_property_schema(return_type, "")


# MARK: - Metadata Building


def _build_metadata(
    func: Callable[..., Any],
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build metadata dict with return type schema if applicable."""
    hints = get_type_hints(func, include_extras=True)
    return_type = hints.get("return")

    resolved_metadata = metadata.copy() if metadata else {}
    resolved_metadata["type"] = "SYSTEM"

    if return_type is not None:
        resolved_metadata["return_type"] = _build_return_schema_from_type(return_type)

    return resolved_metadata
