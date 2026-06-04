# pyright: strict
"""Tool utility functions shared across maivn-graph and maivn-server.

This module provides common operations for working with ToolSpec objects,
extracting names, and handling tool references.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast

# MARK: Tool Names


def extract_tool_names(tools: Iterable[object]) -> list[str]:
    """Extract tool names from ToolSpec objects or dicts.

    Handles both dict representations and ToolSpec objects with a .name attribute.
    Filters out None values to ensure clean name lists.

    Args:
        tools: List of tool objects (dict or ToolSpec instances)

    Returns:
        List of tool name strings (None values filtered out)

    Example:
        >>> tools = [{'name': 'search'}, {'name': 'calculator'}, {'name': None}]
        >>> extract_tool_names(tools)
        ['search', 'calculator']
    """
    names: list[str] = []
    for tool in tools:
        if isinstance(tool, Mapping):
            tool_mapping = cast(Mapping[object, object], tool)
            name = tool_mapping.get("name")
        else:
            name = _get_name_attribute(tool)
        if name is not None:
            names.append(cast(str, name))
    return names


def _get_name_attribute(tool: object) -> object | None:
    return cast(object | None, getattr(tool, "name", None))
