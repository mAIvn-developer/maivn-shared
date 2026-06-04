# pyright: strict
from __future__ import annotations

import pytest
from pydantic import ValidationError

from maivn_shared.domain.entities.swarm_actions import SwarmActionPlan, SwarmAgentAction


def _swarm_action(
    action_id: str,
    *,
    depends_on: list[str] | None = None,
    use_as_final_output: bool = False,
) -> SwarmAgentAction:
    return SwarmAgentAction(
        action_type="swarm_agent",
        id=action_id,
        agent_id=action_id,
        depends_on=depends_on or [],
        use_as_final_output=use_as_final_output,
    )


def test_swarm_action_plan_rejects_unknown_dependencies() -> None:
    with pytest.raises(ValidationError, match="depends_on references unknown action_id"):
        _ = SwarmActionPlan(actions=[_swarm_action("writer", depends_on=["missing"])])


def test_swarm_action_plan_rejects_self_dependencies() -> None:
    with pytest.raises(ValidationError, match="cannot depend on itself"):
        _ = SwarmActionPlan(actions=[_swarm_action("writer", depends_on=["writer"])])


def test_swarm_action_plan_rejects_dependency_cycles() -> None:
    with pytest.raises(ValidationError, match="depends_on cycle"):
        _ = SwarmActionPlan(
            actions=[
                _swarm_action("researcher", depends_on=["writer"]),
                _swarm_action("writer", depends_on=["researcher"]),
            ]
        )


def test_swarm_action_plan_accepts_valid_dag() -> None:
    plan = SwarmActionPlan(
        actions=[
            _swarm_action("researcher"),
            _swarm_action("writer", depends_on=["researcher"], use_as_final_output=True),
        ]
    )

    assert [action.action_id for action in plan.actions] == ["researcher", "writer"]
