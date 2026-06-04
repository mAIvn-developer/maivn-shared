# pyright: strict
from __future__ import annotations

import pytest
from pydantic import ValidationError

from maivn_shared.domain.entities.session_config import (
    MemoryResourceConfig,
    MemorySkillConfig,
    SessionExecutionConfig,
    SessionOrchestrationConfig,
    SwarmAgentConfig,
    SwarmConfig,
    SystemToolsConfig,
    normalize_nested_synthesis,
)

# MARK: Tests


@pytest.mark.parametrize(
    "raw_value,expected",
    [
        (None, None),
        (True, True),
        (False, False),
        ("auto", "auto"),
        (" Auto ", "auto"),
        ("true", True),
        ("YES", True),
        ("0", False),
        ("off", False),
    ],
)
def test_normalize_nested_synthesis_accepts_supported_modes(
    raw_value: object,
    expected: bool | str | None,
) -> None:
    assert normalize_nested_synthesis(raw_value) == expected


@pytest.mark.parametrize("raw_value", [1, 0, object(), "sometimes", ["auto"]])
def test_normalize_nested_synthesis_rejects_unsupported_modes(raw_value: object) -> None:
    with pytest.raises(ValueError, match="included_nested_synthesis"):
        _ = normalize_nested_synthesis(raw_value)


@pytest.mark.parametrize("model_type", [SwarmAgentConfig, SwarmConfig])
def test_nested_synthesis_config_models_reject_unsupported_modes(
    model_type: type[SwarmAgentConfig] | type[SwarmConfig],
) -> None:
    with pytest.raises(ValidationError):
        _ = model_type.model_validate({"included_nested_synthesis": 1})


def test_session_orchestration_config_projects_policy_metadata() -> None:
    config = SessionOrchestrationConfig.model_validate(
        {
            "mode": "SUPERVISOR_LOOP",
            "final_output_mode": "Supervised",
            "allow_followup_actions": True,
            "stop_strategy": "objective_satisfied",
            "allow_reevaluate_loop": True,
            "max_cycles": 5,
        }
    )

    assert config.to_metadata_patch() == {
        "orchestration_mode": "supervisor_loop",
        "final_output_mode": "supervised",
        "allow_followup_actions": True,
        "stop_strategy": "objective_satisfied",
        "allow_reevaluate_loop": True,
        "max_orchestration_cycles": 5,
    }


def test_session_orchestration_config_rejects_unknown_policy_modes() -> None:
    with pytest.raises(ValidationError):
        _ = SessionOrchestrationConfig.model_validate({"mode": "forever"})


# MARK: - Merge Golden Tests (heavy-1 / heavy-2)


def test_execution_config_merge_overrides_set_fields_only() -> None:
    base = SessionExecutionConfig(agent_id="base-agent", timeout=30, client_timezone="UTC")
    override = SessionExecutionConfig(agent_id="override-agent", sdk_delivery_mode="stream")

    merged = base.merged_with(override)

    assert merged.agent_id == "override-agent"
    assert merged.timeout == 30
    assert merged.client_timezone == "UTC"
    assert merged.sdk_delivery_mode == "stream"
    # original untouched
    assert base.agent_id == "base-agent"
    assert base.sdk_delivery_mode is None


def test_execution_config_merge_classmethod_chains_configs() -> None:
    merged = SessionExecutionConfig.merge(
        None,
        SessionExecutionConfig(agent_id="a", timeout=10),
        None,
        SessionExecutionConfig(agent_id="b", client_timezone="America/Chicago"),
    )

    assert merged is not None
    assert merged.agent_id == "b"
    assert merged.timeout == 10
    assert merged.client_timezone == "America/Chicago"


def test_execution_config_merge_returns_none_for_all_empty() -> None:
    assert SessionExecutionConfig.merge(None, SessionExecutionConfig(), None) is None


def test_execution_config_merged_with_empty_override_returns_copy() -> None:
    base = SessionExecutionConfig(agent_id="base", timeout=5)
    merged = base.merged_with(SessionExecutionConfig())
    assert merged is not base
    assert merged.model_dump() == base.model_dump()


def test_system_tools_config_merge_preserves_list_and_bool_fields() -> None:
    base = SystemToolsConfig(allowed_tools=["web_search"], allow_private_data=True)
    override = SystemToolsConfig(
        approved_compose_artifact_targets=True,
        allow_private_data_placeholders=False,
    )

    merged = base.merged_with(override)

    assert merged.allowed_tools == ["web_search"]
    assert merged.allow_private_data is True
    assert merged.approved_compose_artifact_targets is True
    assert merged.allow_private_data_placeholders is False


def test_system_tools_config_merge_override_wins_on_overlap() -> None:
    base = SystemToolsConfig(allowed_tools=["a", "b"])
    override = SystemToolsConfig(allowed_tools=["c"])

    merged = base.merged_with(override)

    assert merged.allowed_tools == ["c"]


def test_orchestration_config_merge_overrides_set_fields_only() -> None:
    base = SessionOrchestrationConfig(mode="supervisor_loop", max_cycles=3)
    override = SessionOrchestrationConfig(
        final_output_mode="terminal",
        allow_followup_actions=True,
    )

    merged = base.merged_with(override)

    assert merged.mode == "supervisor_loop"
    assert merged.max_cycles == 3
    assert merged.final_output_mode == "terminal"
    assert merged.allow_followup_actions is True


def test_orchestration_config_merge_classmethod_chains_configs() -> None:
    merged = SessionOrchestrationConfig.merge(
        SessionOrchestrationConfig(mode="supervisor_loop"),
        None,
        SessionOrchestrationConfig(stop_strategy="max_cycles", max_cycles=7),
    )

    assert merged is not None
    assert merged.mode == "supervisor_loop"
    assert merged.stop_strategy == "max_cycles"
    assert merged.max_cycles == 7


# MARK: - Extra-Key Contract (heavy-9)


def test_memory_skill_config_ignores_unexpected_keys() -> None:
    config = MemorySkillConfig.model_validate({"name": "Skill A", "unexpected_field": "dropped"})

    assert config.name == "Skill A"
    assert "unexpected_field" not in config.to_metadata_payload()


def test_memory_resource_config_ignores_unexpected_keys() -> None:
    config = MemoryResourceConfig.model_validate({"title": "Resource A", "bogus_key": [1, 2, 3]})

    assert config.title == "Resource A"
    assert "bogus_key" not in config.to_metadata_payload()


def test_swarm_agent_config_ignores_unexpected_keys() -> None:
    config = SwarmAgentConfig.model_validate({"agent_id": "agent-1", "stray": "drop"})

    assert config.agent_id == "agent-1"
    assert "stray" not in config.to_metadata_payload()
