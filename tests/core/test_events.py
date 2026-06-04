# pyright: strict
from __future__ import annotations

from maivn_shared import (
    EVALUATING_ENRICHMENT_PHASE,
    EXECUTING_ACTIONS_ENRICHMENT_PHASE,
    FINALIZING_ENRICHMENT_PHASE,
    KNOWN_ENRICHMENT_PHASES,
    MEMORY_ENRICHMENT_PHASES,
    MEMORY_GRAPH_EXTRACTING_ENRICHMENT_PHASE,
    MEMORY_INDEXED_ENRICHMENT_PHASE,
    MEMORY_INDEXING_ENRICHMENT_PHASE,
    MEMORY_INSIGHT_EXTRACTED_ENRICHMENT_PHASE,
    MEMORY_INSIGHT_EXTRACTING_ENRICHMENT_PHASE,
    MEMORY_RETRIEVED_ENRICHMENT_PHASE,
    MEMORY_RETRIEVING_ENRICHMENT_PHASE,
    MEMORY_SKILL_EXTRACTED_ENRICHMENT_PHASE,
    MEMORY_SKILL_EXTRACTING_ENRICHMENT_PHASE,
    MEMORY_SUMMARIZED_ENRICHMENT_PHASE,
    MEMORY_SUMMARIZING_ENRICHMENT_PHASE,
    PROCESSING_ENRICHMENT_MESSAGES,
    PROCESSING_ENRICHMENT_PHASES,
    REEVALUATE_ACCRUED_ENRICHMENT_PHASE,
    RESOURCE_DEDUP_REUSED_ENRICHMENT_PHASE,
    RESOURCE_ENRICHMENT_PHASES,
    RESOURCE_EXTRACTED_ENRICHMENT_PHASE,
    RESOURCE_EXTRACTING_ENRICHMENT_PHASE,
    RESOURCE_REGISTERED_ENRICHMENT_PHASE,
    RESOURCE_REGISTERING_ENRICHMENT_PHASE,
    RESOURCE_VERSION_SUPERSEDED_ENRICHMENT_PHASE,
    is_known_enrichment_phase,
    resolve_enrichment_message,
)

# MARK: Tests


def test_memory_enrichment_phase_constants_are_stable() -> None:
    assert MEMORY_SUMMARIZING_ENRICHMENT_PHASE == "memory_summarizing"
    assert MEMORY_SUMMARIZED_ENRICHMENT_PHASE == "memory_summarized"
    assert MEMORY_RETRIEVING_ENRICHMENT_PHASE == "memory_retrieving"
    assert MEMORY_RETRIEVED_ENRICHMENT_PHASE == "memory_retrieved"
    assert MEMORY_INDEXING_ENRICHMENT_PHASE == "memory_indexing"
    assert MEMORY_INDEXED_ENRICHMENT_PHASE == "memory_indexed"
    assert MEMORY_GRAPH_EXTRACTING_ENRICHMENT_PHASE == "memory_graph_extracting"
    assert MEMORY_SKILL_EXTRACTING_ENRICHMENT_PHASE == "memory_skill_extracting"
    assert MEMORY_INSIGHT_EXTRACTING_ENRICHMENT_PHASE == "memory_insight_extracting"
    assert MEMORY_SKILL_EXTRACTED_ENRICHMENT_PHASE == "memory_skill_extracted"
    assert MEMORY_INSIGHT_EXTRACTED_ENRICHMENT_PHASE == "memory_insight_extracted"


def test_memory_enrichment_phase_registry_contains_all_memory_phases() -> None:
    assert MEMORY_ENRICHMENT_PHASES == (
        MEMORY_SUMMARIZING_ENRICHMENT_PHASE,
        MEMORY_SUMMARIZED_ENRICHMENT_PHASE,
        MEMORY_RETRIEVING_ENRICHMENT_PHASE,
        MEMORY_RETRIEVED_ENRICHMENT_PHASE,
        MEMORY_INDEXING_ENRICHMENT_PHASE,
        MEMORY_INDEXED_ENRICHMENT_PHASE,
        MEMORY_GRAPH_EXTRACTING_ENRICHMENT_PHASE,
        MEMORY_SKILL_EXTRACTING_ENRICHMENT_PHASE,
        MEMORY_INSIGHT_EXTRACTING_ENRICHMENT_PHASE,
        MEMORY_SKILL_EXTRACTED_ENRICHMENT_PHASE,
        MEMORY_INSIGHT_EXTRACTED_ENRICHMENT_PHASE,
    )


def test_resource_enrichment_phase_constants_are_stable() -> None:
    assert RESOURCE_REGISTERING_ENRICHMENT_PHASE == "resource_registering"
    assert RESOURCE_REGISTERED_ENRICHMENT_PHASE == "resource_registered"
    assert RESOURCE_DEDUP_REUSED_ENRICHMENT_PHASE == "resource_dedup_reused"
    assert RESOURCE_VERSION_SUPERSEDED_ENRICHMENT_PHASE == "resource_version_superseded"
    assert RESOURCE_EXTRACTING_ENRICHMENT_PHASE == "resource_extracting"
    assert RESOURCE_EXTRACTED_ENRICHMENT_PHASE == "resource_extracted"


def test_resource_enrichment_phase_registry_contains_all_resource_phases() -> None:
    assert RESOURCE_ENRICHMENT_PHASES == (
        RESOURCE_REGISTERING_ENRICHMENT_PHASE,
        RESOURCE_REGISTERED_ENRICHMENT_PHASE,
        RESOURCE_DEDUP_REUSED_ENRICHMENT_PHASE,
        RESOURCE_VERSION_SUPERSEDED_ENRICHMENT_PHASE,
        RESOURCE_EXTRACTING_ENRICHMENT_PHASE,
        RESOURCE_EXTRACTED_ENRICHMENT_PHASE,
    )


# MARK: Processing phases


def test_processing_enrichment_phase_constants_are_stable() -> None:
    assert EVALUATING_ENRICHMENT_PHASE == "evaluating"
    assert EXECUTING_ACTIONS_ENRICHMENT_PHASE == "executing_actions"
    assert FINALIZING_ENRICHMENT_PHASE == "finalizing"
    assert REEVALUATE_ACCRUED_ENRICHMENT_PHASE == "reevaluate_accrued"


def test_processing_messages_cover_every_processing_phase() -> None:
    # Every processing phase must have a display message (single source of truth
    # consumed by the server + SDK).
    assert set(PROCESSING_ENRICHMENT_PHASES) == set(PROCESSING_ENRICHMENT_MESSAGES)
    assert all(message for message in PROCESSING_ENRICHMENT_MESSAGES.values())


def test_resolve_enrichment_message_prefers_explicit_then_canonical_then_phase() -> None:
    # Explicit message wins.
    assert resolve_enrichment_message("planning", "Custom") == "Custom"
    # Falls back to the canonical processing map.
    assert resolve_enrichment_message(FINALIZING_ENRICHMENT_PHASE) == "Finalizing response..."
    # Unknown phase with no message degrades to the raw phase string.
    assert resolve_enrichment_message("totally_unknown") == "totally_unknown"


def test_known_enrichment_phases_union_is_complete() -> None:
    assert is_known_enrichment_phase(FINALIZING_ENRICHMENT_PHASE)
    assert is_known_enrichment_phase(REEVALUATE_ACCRUED_ENRICHMENT_PHASE)
    assert not is_known_enrichment_phase("totally_unknown")
    for phase in (
        *PROCESSING_ENRICHMENT_PHASES,
        *MEMORY_ENRICHMENT_PHASES,
        *RESOURCE_ENRICHMENT_PHASES,
        REEVALUATE_ACCRUED_ENRICHMENT_PHASE,
    ):
        assert phase in KNOWN_ENRICHMENT_PHASES
