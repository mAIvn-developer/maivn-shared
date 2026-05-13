from __future__ import annotations

import types
from dataclasses import fields
from typing import Any, get_args, get_origin, get_type_hints

# MARK: - Type Unwrapping Utilities


def unwrap_annotated(field_type: Any) -> tuple[Any, str]:
    """Unwrap Annotated type and extract description if present.

    Args:
        field_type: The type annotation to unwrap

    Returns:
        Tuple of (unwrapped_type, description)
    """
    description = ""
    origin = get_origin(field_type)

    if origin and getattr(origin, "__name__", "") == "Annotated":
        args = get_args(field_type)
        if args:
            field_type = args[0]
            for arg in args[1:]:
                if isinstance(arg, str):
                    description = arg
                    break

    return field_type, description


def _unwrap_not_required(field_type: Any) -> Any:
    """Unwrap NotRequired type wrapper.

    Args:
        field_type: The type annotation to unwrap

    Returns:
        The inner type if NotRequired, otherwise the original type
    """
    origin = get_origin(field_type)

    if origin and "NotRequired" in getattr(origin, "__name__", ""):
        args = get_args(field_type)
        if args:
            return args[0]

    return field_type


def _unwrap_type(field_type: Any, description: str) -> tuple[Any, str]:
    """Fully unwrap a type annotation, handling Annotated and NotRequired.

    Args:
        field_type: The type annotation to unwrap
        description: Existing description (may be overridden by Annotated metadata)

    Returns:
        Tuple of (fully_unwrapped_type, description)
    """
    field_type, annotated_desc = unwrap_annotated(field_type)
    if annotated_desc and not description:
        description = annotated_desc

    field_type = _unwrap_not_required(field_type)

    field_type, nested_desc = unwrap_annotated(field_type)
    if nested_desc and not description:
        description = nested_desc

    return field_type, description


# MARK: - Primitive Type Handling


_PRIMITIVE_TYPE_MAP: dict[Any, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}

_PRIMITIVE_STRING_MAP: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
}


def _get_primitive_type(field_type: Any) -> str | None:
    """Get JSON schema type for primitive Python types.

    Args:
        field_type: The type to check

    Returns:
        JSON schema type string if primitive, None otherwise
    """
    if field_type in _PRIMITIVE_TYPE_MAP:
        return _PRIMITIVE_TYPE_MAP[field_type]

    if isinstance(field_type, str) and field_type in _PRIMITIVE_STRING_MAP:
        return _PRIMITIVE_STRING_MAP[field_type]

    return None


# MARK: - Container Type Handling


def _is_list_type(origin: Any, field_type: Any) -> bool:
    """Check if the type is a list type."""
    if origin is list:
        return True
    return hasattr(field_type, "__origin__") and field_type.__origin__ is list


def _is_dict_type(origin: Any, field_type: Any) -> bool:
    """Check if the type is a dict type."""
    if origin is dict:
        return True
    return hasattr(field_type, "__origin__") and field_type.__origin__ is dict


def _build_list_schema(args: tuple[Any, ...]) -> dict[str, Any]:
    """Build JSON schema for list types.

    Args:
        args: Type arguments for the list

    Returns:
        JSON schema dict for the list
    """
    schema: dict[str, Any] = {"type": "array"}
    if args:
        schema["items"] = build_property_schema(args[0], "")
    return schema


def _build_dict_schema() -> dict[str, Any]:
    """Build JSON schema for dict types.

    Returns:
        JSON schema dict for the dict
    """
    return {"type": "object"}


# MARK: - Union Type Handling


def _is_union_type(origin: Any) -> bool:
    """Check if the origin represents a Union type (typing.Union or PEP 604 X | Y)."""
    if origin is None:
        return False
    if origin is types.UnionType:
        return True
    origin_name = getattr(origin, "__name__", "")
    return "Union" in origin_name


def _build_union_schema(args: tuple[Any, ...], description: str) -> dict[str, Any]:
    """Build JSON schema for Union types.

    Args:
        args: Type arguments for the union
        description: Description for the schema

    Returns:
        JSON schema dict for the union
    """
    non_none_args = [arg for arg in args if arg is not type(None)]

    if len(non_none_args) == 1:
        return build_property_schema(non_none_args[0], description)

    return {"anyOf": [build_property_schema(arg, "") for arg in non_none_args]}


# MARK: - Schema Building


def build_property_schema(field_type: Any, description: str) -> dict[str, Any]:
    """Build a JSON schema property from a Python type annotation.

    Args:
        field_type: The Python type annotation
        description: Description for the property

    Returns:
        JSON schema dict for the property
    """
    field_type, description = _unwrap_type(field_type, description)

    schema: dict[str, Any] = {}

    if description:
        schema["description"] = description

    primitive_type = _get_primitive_type(field_type)
    if primitive_type:
        schema["type"] = primitive_type
        return schema

    origin = get_origin(field_type)
    args = get_args(field_type)

    if _is_list_type(origin, field_type):
        list_schema = _build_list_schema(args)
        schema.update(list_schema)
    elif _is_dict_type(origin, field_type):
        dict_schema = _build_dict_schema()
        schema.update(dict_schema)
    elif _is_union_type(origin):
        union_schema = _build_union_schema(args, description)
        if "description" in schema and "description" not in union_schema:
            union_schema["description"] = schema["description"]
        return union_schema
    else:
        schema["type"] = "string"

    return schema


# MARK: - Dataclass Schema Building


def build_dataclass_schema(dc: type) -> dict[str, Any]:
    """Build JSON schema from a dataclass.

    Args:
        dc: The dataclass type

    Returns:
        JSON schema dict for the dataclass
    """
    properties: dict[str, Any] = {}
    hints = get_type_hints(dc, include_extras=True)

    for field in fields(dc):
        field_type = hints.get(field.name, field.type)
        field_doc = _extract_field_description(field)

        prop_schema = build_property_schema(field_type, field_doc)
        properties[field.name] = prop_schema

    return {
        "type": "object",
        "properties": properties,
    }


def _extract_field_description(field: Any) -> str:
    """Extract description from a dataclass field's metadata.

    Args:
        field: The dataclass field

    Returns:
        Description string or empty string
    """
    if field.metadata and "description" in field.metadata:
        return field.metadata["description"]
    return ""
