"""Tool utility functions shared across maivn-graph and maivn-server.

This module provides common operations for working with ToolSpec objects,
extracting names, and handling tool references.
"""

from __future__ import annotations

from typing import Any


def extract_tool_names(tools: list[dict | Any]) -> list[str]:
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
    return [
        name
        for tool in tools
        if (name := tool.get("name") if isinstance(tool, dict) else getattr(tool, "name", None))
        is not None
    ]
