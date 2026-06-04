# pyright: strict
from __future__ import annotations

import types
from dataclasses import Field as DataclassField
from dataclasses import fields
from typing import ClassVar, Protocol, TypeAlias, cast, get_args, get_origin, get_type_hints

from pydantic import JsonValue

# MARK: - Types

JsonSchema: TypeAlias = dict[str, JsonValue]


# MARK: - Protocols


class DataclassLike(Protocol):
    __dataclass_fields__: ClassVar[dict[str, DataclassField[object]]]


# MARK: - Type Introspection Helpers

_NONE_TYPE = type(None)


def type_origin(annotation: object) -> object | None:
    """Return typing origin with Any erased at the introspection boundary."""
    return cast(object | None, get_origin(annotation))


def type_args(annotation: object) -> tuple[object, ...]:
    """Return typing args with Any erased at the introspection boundary."""
    return cast(tuple[object, ...], get_args(annotation))


def type_hints(obj: object) -> dict[str, object]:
    """Return type hints with Any erased at the introspection boundary."""
    return cast(dict[str, object], get_type_hints(obj, include_extras=True))


def type_name(annotation: object) -> str:
    """Return a best-effort display name for a type-like object."""
    name = cast(object, getattr(annotation, "__name__", ""))
    return name if isinstance(name, str) else str(name)


def _legacy_origin(annotation: object) -> object | None:
    """Return legacy __origin__ for older typing aliases."""
    return cast(object | None, getattr(annotation, "__origin__", None))


# MARK: - Type Unwrapping Utilities


def unwrap_annotated(field_type: object) -> tuple[object, str]:
    """Unwrap Annotated type and extract description if present.

    Args:
        field_type: The type annotation to unwrap

    Returns:
        Tuple of (unwrapped_type, description)
    """
    description = ""
    origin = type_origin(field_type)

    if origin and type_name(origin) == "Annotated":
        args = type_args(field_type)
        if args:
            field_type = args[0]
            for arg in args[1:]:
                if isinstance(arg, str):
                    description = arg
                    break

    return field_type, description


def _unwrap_not_required(field_type: object) -> object:
    """Unwrap NotRequired type wrapper.

    Args:
        field_type: The type annotation to unwrap

    Returns:
        The inner type if NotRequired, otherwise the original type
    """
    origin = type_origin(field_type)

    if origin and "NotRequired" in type_name(origin):
        args = type_args(field_type)
        if args:
            return args[0]

    return field_type


def _unwrap_type(field_type: object, description: str) -> tuple[object, str]:
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


_PRIMITIVE_TYPE_MAP: dict[object, str] = {
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


def _get_primitive_type(field_type: object) -> str | None:
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


def _is_list_type(origin: object | None, field_type: object) -> bool:
    """Check if the type is a list type."""
    if origin is list:
        return True
    return _legacy_origin(field_type) is list


def _is_dict_type(origin: object | None, field_type: object) -> bool:
    """Check if the type is a dict type."""
    if origin is dict:
        return True
    return _legacy_origin(field_type) is dict


def _build_list_schema(args: tuple[object, ...]) -> JsonSchema:
    """Build JSON schema for list types.

    Args:
        args: Type arguments for the list

    Returns:
        JSON schema dict for the list
    """
    schema: JsonSchema = {"type": "array"}
    if args:
        schema["items"] = build_property_schema(args[0], "")
    return schema


def _build_dict_schema() -> JsonSchema:
    """Build JSON schema for dict types.

    Returns:
        JSON schema dict for the dict
    """
    return {"type": "object"}


# MARK: - Union Type Handling


def _is_union_type(origin: object | None) -> bool:
    """Check if the origin represents a Union type (typing.Union or PEP 604 X | Y)."""
    if origin is None:
        return False
    if origin is types.UnionType:
        return True
    origin_name = type_name(origin)
    return "Union" in origin_name


def _build_union_schema(args: tuple[object, ...], description: str) -> JsonSchema:
    """Build JSON schema for Union types.

    Args:
        args: Type arguments for the union
        description: Description for the schema

    Returns:
        JSON schema dict for the union
    """
    non_none_args = [arg for arg in args if arg is not _NONE_TYPE]

    if len(non_none_args) == 1:
        return build_property_schema(non_none_args[0], description)

    return {"anyOf": cast(JsonValue, [build_property_schema(arg, "") for arg in non_none_args])}


# MARK: - Schema Building


def build_property_schema(field_type: object, description: str) -> JsonSchema:
    """Build a JSON schema property from a Python type annotation.

    Args:
        field_type: The Python type annotation
        description: Description for the property

    Returns:
        JSON schema dict for the property
    """
    field_type, description = _unwrap_type(field_type, description)

    schema: JsonSchema = {}

    if description:
        schema["description"] = description

    primitive_type = _get_primitive_type(field_type)
    if primitive_type:
        schema["type"] = primitive_type
        return schema

    origin = type_origin(field_type)
    args = type_args(field_type)

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


# MARK: - Object Schema Building


def build_object_schema(properties: dict[str, JsonValue]) -> JsonSchema:
    """Wrap a properties map in the canonical ``{"type": "object", ...}`` envelope.

    Shared by every factory path that emits an object schema (args schemas,
    dataclass schemas, and return-type schemas) so the envelope shape stays
    consistent across modules.
    """
    return {
        "type": "object",
        "properties": cast(JsonValue, properties),
    }


# MARK: - Dataclass Schema Building


def build_dataclass_schema(dc: type[object]) -> JsonSchema:
    """Build JSON schema from a dataclass.

    Args:
        dc: The dataclass type

    Returns:
        JSON schema dict for the dataclass
    """
    properties: dict[str, JsonValue] = {}
    hints = type_hints(dc)

    dataclass_fields = fields(cast(type[DataclassLike], dc))
    for field in cast(tuple[DataclassField[object], ...], dataclass_fields):
        field_type = hints.get(field.name, cast(object, field.type))
        field_doc = _extract_field_description(field)

        prop_schema = build_property_schema(field_type, field_doc)
        properties[field.name] = prop_schema

    return build_object_schema(properties)


def _extract_field_description(field: DataclassField[object]) -> str:
    """Extract description from a dataclass field's metadata.

    Args:
        field: The dataclass field

    Returns:
        Description string or empty string
    """
    metadata = cast(dict[str, object], dict(field.metadata))
    description = metadata.get("description")
    if isinstance(description, str):
        return description
    return ""
