from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SkipValidation,
    field_serializer,
    field_validator,
)

# MARK: Type Aliases

TypeBaseModel = type[BaseModel]
ArgsSchema = TypeBaseModel | dict[str, Any]

# MARK: Tool Type

ToolType = Literal["func", "model", "agent", "system", "mcp"]

# MARK: - Constants

_DEFAULT_PRIVATE_DATA_KEY = "__private_data__"


class ToolSpec(BaseModel):
    """Specification for a tool that can be executed by an agent."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    # MARK: - Core Identification

    tool_id: str = Field(..., description="Deterministic UUID tool identifier")
    agent_id: str = Field(..., description="Agent ID that owns this tool")
    name: str = Field(
        ...,
        description="Unique tool name. Use a stable, identifier-friendly name.",
        json_schema_extra={"examples": ["userprofile_main", "finalize_report"]},
    )
    description: str = Field(
        ...,
        description=(
            "Human-readable description of what the tool does and when to use it. "
            "Include important constraints or side effects if applicable."
        ),
        json_schema_extra={"examples": ["Summarize a PDF into key highlights and a short brief."]},
    )
    tags: list[str] | None = Field(
        default_factory=list,
        description="List of tags to categorize the tool",
    )

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, value: Any) -> Any:
        if value is None:
            return []
        return value

    # MARK: - Type and Schema

    tool_type: ToolType = Field(
        default="func",
        description="Type of tool (function or model)",
    )
    args_schema: Annotated[ArgsSchema, SkipValidation()] = Field(  # type: ignore
        ...,
        description="Tool schema without $defs, dependencies in properties",
    )

    # MARK: - Execution Flags

    always_execute: bool = Field(
        default=False,
        description=(
            "Whether this tool must always be executed in every invocation. "
            "Note: Dependencies are automatically enforced via schema references. "
            "This flag is for standalone tools that must run regardless of whether they're "
            "needed for the current request. Common in chat bot scenarios."
        ),
    )
    final_tool: bool | None = Field(
        default=False,
        description="Final output of the tool (if applicable)",
    )
    metadata: dict[str, Any] | None = Field(
        default_factory=dict,
        description="Additional metadata for the tool",
    )

    @field_validator("metadata", mode="before")
    @classmethod
    def _coerce_metadata(cls, value: Any) -> Any:
        if value is None:
            return {}
        return value

    # MARK: - Public API

    def get_dependency_names(
        self,
        *,
        include_data: bool = False,
        include_interrupt: bool = False,
    ) -> list[str]:
        """Extract dependency identifiers from the args_schema.

        Args:
            include_data: Whether to include data dependencies.
            include_interrupt: Whether to include interrupt dependencies.

        Returns:
            Ordered list of dependency identifiers (first match per property).
        """
        names: list[str] = []
        for prop_schema in self._get_schema_properties().values():
            for dep in self._iter_dependencies(prop_schema):
                dep_type, _, name = dep
                if dep_type == "tool" and name:
                    names.append(name)
                    break
                if dep_type == "data" and include_data and name:
                    names.append(name)
                    break
                if dep_type == "interrupt" and include_interrupt and name:
                    names.append(name)
                    break
        return names

    def get_dependency_ids(self) -> list[str]:
        """Extract ALL tool dependency IDs from the args_schema.

        Returns tool_id values for database lookups. Collects all IDs from
        union types (anyOf/oneOf) to properly resolve union dependencies.

        Returns:
            Ordered list of tool dependency IDs (excludes data/interrupt deps).
        """
        ids: list[str] = []
        for prop_schema in self._get_schema_properties().values():
            for dep_type, tool_id, _ in self._iter_dependencies(prop_schema):
                if dep_type == "tool" and tool_id:
                    ids.append(tool_id)
        return ids

    # MARK: - Private Methods

    def _get_schema_properties(self) -> dict[str, Any]:
        """Get properties dictionary from args_schema."""
        schema = self._get_args_schema_dict()
        return schema.get("properties", {})

    def _get_args_schema_dict(self) -> dict[str, Any]:
        """Return args_schema as a dictionary for inspection."""
        schema = self.args_schema

        if isinstance(schema, dict):
            return schema

        if isinstance(schema, type) and issubclass(schema, BaseModel):
            return self._model_to_schema(schema)

        if isinstance(schema, BaseModel):
            return schema.model_json_schema()

        return {}

    @staticmethod
    def _model_to_schema(model: type[BaseModel]) -> dict[str, Any]:
        """Convert a Pydantic model class to JSON schema."""
        try:
            return model.model_json_schema()
        except AttributeError:
            return {}

    @staticmethod
    def _iter_dependencies(
        prop_schema: Any,
    ) -> Iterator[tuple[str, str | None, str | None]]:
        """Iterate over all dependencies in a property schema.

        Yields tuples of (dep_type, tool_id, name) where:
        - dep_type: 'tool', 'data', or 'interrupt'
        - tool_id: The tool_id (for tool dependencies)
        - name: The dependency name (tool_name, data_key, or interrupt_id)

        Handles direct types, anyOf/oneOf unions, arrays, and additionalProperties.
        """
        if not isinstance(prop_schema, dict):
            return

        dep_type = prop_schema.get("type")

        # Direct dependency types
        if dep_type == "tool_dependency":
            tool_id = prop_schema.get("tool_id")
            name = prop_schema.get("tool_name") or tool_id
            yield ("tool", tool_id, name)
            return

        if dep_type == "data_dependency":
            data_key = prop_schema.get("data_key") or prop_schema.get("arg_name")
            yield ("data", None, data_key or _DEFAULT_PRIVATE_DATA_KEY)
            return

        if dep_type == "interrupt_dependency":
            yield ("interrupt", None, prop_schema.get("interrupt_id"))
            return

        # Handle anyOf/oneOf union types - yield all matches
        for union_key in ("anyOf", "oneOf"):
            union_schemas = prop_schema.get(union_key)
            if isinstance(union_schemas, list):
                for sub_schema in union_schemas:
                    yield from ToolSpec._iter_dependencies(sub_schema)

        # Handle array items: list[UnionType] -> {"type": "array", "items": {...}}
        if dep_type == "array":
            items_schema = prop_schema.get("items")
            if isinstance(items_schema, dict):
                yield from ToolSpec._iter_dependencies(items_schema)

        # Handle dict values: dict[str, UnionType] -> {"additionalProperties": {...}}
        additional_props = prop_schema.get("additionalProperties")
        if isinstance(additional_props, dict):
            yield from ToolSpec._iter_dependencies(additional_props)

    # MARK: - Serializers

    @field_serializer("tool_type", when_used="always")
    def _serialize_tool_type(self, value: ToolType) -> str:
        return value

    @field_serializer("args_schema", when_used="always")
    def _serialize_args_schema(self, value: ArgsSchema) -> dict[str, Any] | str | None:
        if isinstance(value, type) and issubclass(value, BaseModel):
            return self._model_to_schema(value)

        if isinstance(value, dict):
            return value

        return str(value) if value is not None else None
