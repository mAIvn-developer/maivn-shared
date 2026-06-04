# pyright: strict
from __future__ import annotations

import pytest
from pydantic import ValidationError

from maivn_shared import MemoryConfig, MemoryInsightExtractionConfig, MemoryRetrievalConfig

# MARK: Tests


def test_memory_insight_extraction_config_accepts_agent_or_swarm_scope() -> None:
    agent_scope = MemoryInsightExtractionConfig(sharing_scope="agent")
    swarm_scope = MemoryInsightExtractionConfig.model_validate({"sharing_scope": "SWARM"})

    assert agent_scope.sharing_scope == "agent"
    assert swarm_scope.sharing_scope == "swarm"


def test_memory_insight_extraction_config_rejects_project_or_org_scope() -> None:
    with pytest.raises(ValidationError, match="agent"):
        _ = MemoryInsightExtractionConfig.model_validate({"sharing_scope": "project"})

    with pytest.raises(ValidationError, match="swarm"):
        _ = MemoryInsightExtractionConfig.model_validate({"sharing_scope": "org"})


def test_memory_config_rejects_project_scope_for_auto_insight_extraction() -> None:
    with pytest.raises(ValidationError, match="agent"):
        _ = MemoryConfig.model_validate(
            {
                "insight_extraction": {
                    "enabled": True,
                    "sharing_scope": "project",
                }
            }
        )


def test_memory_retrieval_config_prefers_resource_field_names() -> None:
    retrieval = MemoryRetrievalConfig(
        resources_enabled=True,
        resource_injection_max_count=3,
    )

    assert retrieval.resources_enabled is True
    assert retrieval.resource_injection_max_count == 3
    assert retrieval.model_dump(exclude_none=True) == {
        "resources_enabled": True,
        "resource_injection_max_count": 3,
    }


def test_memory_retrieval_config_accepts_resource_fields() -> None:
    retrieval = MemoryRetrievalConfig.model_validate(
        {
            "resources_enabled": True,
            "resource_injection_max_count": 2,
        }
    )

    assert retrieval.resources_enabled is True
    assert retrieval.resource_injection_max_count == 2
