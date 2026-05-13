from __future__ import annotations

import pytest
from pydantic import ValidationError

from maivn_shared.domain.entities.session_config import (
    SessionOrchestrationConfig,
    SwarmAgentConfig,
    SwarmConfig,
    normalize_nested_synthesis,
)


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
        normalize_nested_synthesis(raw_value)


@pytest.mark.parametrize("model_type", [SwarmAgentConfig, SwarmConfig])
def test_nested_synthesis_config_models_reject_unsupported_modes(
    model_type: type[SwarmAgentConfig] | type[SwarmConfig],
) -> None:
    with pytest.raises(ValidationError):
        model_type.model_validate({"included_nested_synthesis": 1})


def test_session_orchestration_config_projects_policy_metadata() -> None:
    # Pass case-variant strings to exercise the `mode="before"` normalizer that
    # lowercases input. The static Literal[...] types only accept the canonical
    # lowercase form, so silence the type checker for these intentional inputs.
    config = SessionOrchestrationConfig(
        mode="SUPERVISOR_LOOP",  # pyright: ignore[reportArgumentType]
        final_output_mode="Supervised",  # pyright: ignore[reportArgumentType]
        allow_followup_actions=True,
        stop_strategy="objective_satisfied",
        allow_reevaluate_loop=True,
        max_cycles=5,
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
    # "forever" is intentionally not a valid mode; the assertion is that the
    # validator rejects it. Silence pyright for the deliberately invalid input.
    with pytest.raises(ValidationError):
        SessionOrchestrationConfig(mode="forever")  # pyright: ignore[reportArgumentType]
