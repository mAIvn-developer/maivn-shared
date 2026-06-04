# pyright: strict
"""Factory for dynamically generating ToolSpecs from functions and agent state schemas.

This module provides utilities to generate ToolSpec instances from:
1. Async functions (using signatures, docstrings, and type annotations)
2. TypedDict-based agent states

This eliminates the need for manual schema duplication and maintenance.
"""

from __future__ import annotations

# MARK: - Function Factory
from .function_factory import build_tool_spec_from_function

# MARK: - State Factory
from .state_factory import build_tool_spec_from_state

__all__ = [
    # MARK: - Function Factory
    "build_tool_spec_from_function",
    # MARK: - State Factory
    "build_tool_spec_from_state",
]
