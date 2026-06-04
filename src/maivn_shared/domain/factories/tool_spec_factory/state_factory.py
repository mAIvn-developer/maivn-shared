# pyright: strict
from __future__ import annotations

from typing import cast

from pydantic import JsonValue

from ...entities.tool_spec import ToolSpec, ToolType
from .schema_utils import (
    JsonSchema,
    build_object_schema,
    build_property_schema,
    type_args,
    type_hints,
    type_name,
    type_origin,
    unwrap_annotated,
)

# MARK: - Public API


def build_tool_spec_from_state(
    *,
    state_class: type[object],
    tool_id: str,
    agent_id: str,
    name: str,
    description: str,
    tool_type: ToolType = "agent",
    input_fields: list[str] | None = None,
    output_fields: list[str] | None = None,
    required_fields: list[str] | None = None,
    metadata: dict[str, object] | None = None,
    always_execute: bool = False,
    final_tool: bool = False,
) -> ToolSpec:
    """Build a ToolSpec dynamically from an agent state TypedDict."""
    hints = type_hints(state_class)
    field_docs = _extract_field_docs(state_class)

    resolved_input_fields = _resolve_input_fields(hints, input_fields, output_fields)
    resolved_required_fields = _resolve_required_fields(
        hints, resolved_input_fields, required_fields
    )

    args_schema = _build_args_schema(
        hints, resolved_input_fields, resolved_required_fields, field_docs
    )
    resolved_metadata = _build_metadata(hints, output_fields, field_docs, metadata)

    return ToolSpec(
        tool_id=tool_id,
        agent_id=agent_id,
        name=name,
        description=description,
        tool_type=tool_type,
        args_schema=args_schema,
        always_execute=always_execute,
        final_tool=final_tool,
        metadata=cast(JsonSchema, resolved_metadata),
    )


# MARK: - Field Resolution


def _resolve_input_fields(
    hints: dict[str, object],
    input_fields: list[str] | None,
    output_fields: list[str] | None,
) -> list[str]:
    """Resolve input fields from hints or explicit list."""
    if input_fields is not None:
        return input_fields

    excluded = set(output_fields or []) | {"messages"}
    return [f for f in hints if not f.startswith("_") and f not in excluded]


def _resolve_required_fields(
    hints: dict[str, object],
    input_fields: list[str],
    required_fields: list[str] | None,
) -> list[str]:
    """Resolve required fields from hints or explicit list."""
    if required_fields is not None:
        return required_fields

    return [f for f in input_fields if not _is_not_required(hints.get(f))]


def _is_not_required(field_type: object | None) -> bool:
    """Check if a field is annotated with NotRequired."""
    if field_type is None:
        return False

    # Unwrap Annotated wrapper if present, then check inner type
    unwrapped, _ = unwrap_annotated(field_type)
    origin = type_origin(unwrapped)
    if origin is not None and "NotRequired" in type_name(origin):
        return True

    return False


# MARK: - Schema Building


def _build_args_schema(
    hints: dict[str, object],
    input_fields: list[str],
    required_fields: list[str],
    field_docs: dict[str, str],
) -> JsonSchema:
    """Build args schema from input fields."""
    properties = _build_properties(hints, input_fields, field_docs)

    schema = build_object_schema(properties)
    schema["required"] = cast(JsonValue, required_fields)
    return schema


def _build_properties(
    hints: dict[str, object],
    fields: list[str],
    field_docs: dict[str, str],
) -> JsonSchema:
    """Build property schemas for given fields."""
    properties: JsonSchema = {}

    for field_name in fields:
        if field_name not in hints:
            continue

        field_type = hints[field_name]
        field_doc = field_docs.get(field_name, "")
        properties[field_name] = build_property_schema(field_type, field_doc)

    return properties


def _build_return_type_schema_from_fields(
    hints: dict[str, object],
    output_fields: list[str],
    field_docs: dict[str, str],
) -> JsonSchema:
    """Build a return-type schema from a state's output fields."""
    properties = _build_properties(hints, output_fields, field_docs)

    return build_object_schema(properties)


# MARK: - Metadata Building


def _build_metadata(
    hints: dict[str, object],
    output_fields: list[str] | None,
    field_docs: dict[str, str],
    metadata: dict[str, object] | None,
) -> dict[str, object]:
    """Build metadata dict with output fields if applicable."""
    resolved_metadata: dict[str, object] = metadata.copy() if metadata else {}

    if output_fields:
        resolved_metadata["output_fields"] = output_fields
        resolved_metadata["return_type"] = _build_return_type_schema_from_fields(
            hints, output_fields, field_docs
        )

    return resolved_metadata


# MARK: - Documentation Extraction


def _extract_field_docs(state_class: type[object]) -> dict[str, str]:
    """Extract field documentation from Annotated metadata or class docstring."""
    hints = type_hints(state_class)

    field_docs = _extract_annotated_docs(hints)
    _extract_docstring_docs(state_class, hints, field_docs)

    return field_docs


def _extract_annotated_docs(hints: dict[str, object]) -> dict[str, str]:
    """Extract documentation from Annotated type hints."""
    field_docs: dict[str, str] = {}

    for field_name, field_type in hints.items():
        origin = type_origin(field_type)
        if origin is None or type_name(origin) != "Annotated":
            continue

        args = type_args(field_type)
        if len(args) <= 1:
            continue

        for arg in args[1:]:
            if isinstance(arg, str):
                field_docs[field_name] = arg
                break

    return field_docs


def _extract_docstring_docs(
    state_class: type[object],
    hints: dict[str, object],
    field_docs: dict[str, str],
) -> None:
    """Extract documentation from class docstring into field_docs."""
    docstring = state_class.__doc__
    if not docstring:
        return

    for line in docstring.split("\n"):
        stripped = line.strip()
        if ":" not in stripped or stripped.startswith("#"):
            continue

        parts = stripped.split(":", 1)
        if len(parts) != 2:
            continue

        field_name = parts[0].strip()
        if field_name in hints and field_name not in field_docs:
            field_docs[field_name] = parts[1].strip()
