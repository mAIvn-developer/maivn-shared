# pyright: strict
from __future__ import annotations

from maivn_shared.domain.entities.tool_spec import JsonObject, ToolSpec

# MARK: Helpers


def _make_tool_spec(*, final_tool: bool | None = None) -> ToolSpec:
    args_schema: JsonObject = {"type": "object", "properties": {}}
    if final_tool is None:
        return ToolSpec(
            tool_id="tool-1",
            agent_id="agent-1",
            name="demo_tool",
            description="A demo tool.",
            args_schema=args_schema,
        )
    return ToolSpec(
        tool_id="tool-1",
        agent_id="agent-1",
        name="demo_tool",
        description="A demo tool.",
        args_schema=args_schema,
        final_tool=final_tool,
    )


# MARK: Tests


def test_tool_spec_final_tool_defaults_to_false_when_omitted() -> None:
    spec = _make_tool_spec()

    assert spec.final_tool is False


def test_tool_spec_final_tool_accepts_true() -> None:
    spec = _make_tool_spec(final_tool=True)

    assert spec.final_tool is True


def test_tool_spec_dependency_ids_include_return_type_dependencies() -> None:
    spec = ToolSpec(
        tool_id="tool-1",
        agent_id="agent-1",
        name="demo_tool",
        description="A demo tool.",
        args_schema={
            "type": "object",
            "properties": {},
            "return_type": {
                "type": "tool_dependency",
                "tool_id": "uuid-output-model",
                "tool_name": "OutputModel",
            },
        },
    )

    assert spec.get_dependency_ids() == ["uuid-output-model"]
    assert spec.get_dependency_names() == ["OutputModel"]
