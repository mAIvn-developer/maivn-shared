# pyright: strict
"""Reserved session-config metadata-key registry."""

from __future__ import annotations

_SYSTEM_TOOLS_METADATA_KEYS = {
    "allowed_system_tools",
    "approved_compose_artifact_targets",
    "allow_private_data_in_system_tools",
    "allow_private_data_placeholders_in_system_tools",
}
_EXECUTION_METADATA_KEYS = {
    "agent_id",
    "client_timezone",
    "maivn_sdk_delivery_mode",
    "sdk_deployment_timezone",
    "server_deployment_timezone",
    "timeout",
}
_STRUCTURED_OUTPUT_METADATA_KEYS = {"structured_output_intent", "structured_output_model"}
_ORCHESTRATION_METADATA_KEYS = {
    "allow_followup_actions",
    "allow_reevaluate_loop",
    "final_output_mode",
    "max_orchestration_cycles",
    "orchestration_mode",
    "stop_strategy",
}
_MEMORY_ASSETS_METADATA_KEYS = {
    "memory_defined_skills",
    "memory_bound_resources",
    "memory_recall_turn_active",
}
_SWARM_METADATA_KEYS = {
    "swarm_invocation_intent",
    "swarm_id",
    "swarm_name",
    "swarm_description",
    "swarm_system_prompt",
    "swarm_agent_roster",
    "swarm_agent_invocation_tool_map",
    "swarm_agent_invocation",
    "swarm_use_as_final_output",
    "swarm_invoked_agent_id",
    "swarm_invoked_agent_name",
    "swarm_included_nested_synthesis",
    "maivn_sdk_delivery_mode",
    "swarm_agent_dependency_context",
    "swarm_agent_dependency_context_keys",
}
RESERVED_SESSION_CONFIG_METADATA_KEYS = frozenset(
    _SYSTEM_TOOLS_METADATA_KEYS
    | _EXECUTION_METADATA_KEYS
    | _STRUCTURED_OUTPUT_METADATA_KEYS
    | _ORCHESTRATION_METADATA_KEYS
    | _MEMORY_ASSETS_METADATA_KEYS
    | _SWARM_METADATA_KEYS
)


# MARK: Reserved-Key Check


def is_reserved_session_config_metadata_key(key: str) -> bool:
    """Return True if ``key`` is in the reserved session-config namespace.

    Session-config metadata keys (``orchestration_mode``, ``stop_strategy``,
    etc.) are projected onto the request from the typed config models and
    cannot be overridden via the free-form ``metadata`` dict.
    """
    return key.strip() in RESERVED_SESSION_CONFIG_METADATA_KEYS


__all__ = [
    "RESERVED_SESSION_CONFIG_METADATA_KEYS",
    "is_reserved_session_config_metadata_key",
]
