"""Shared event-name constants used across Maivn services and SDK."""

from __future__ import annotations

# MARK: - Tool Events

TOOL_EVENT_NAME = "tool_event"
"""Primary event name emitted by the server bridge and consumed by the SDK."""

INTERRUPT_REQUEST_EVENT_NAME = "interrupt_request"
"""Interrupt request event emitted when a tool requires user input."""

INTERRUPT_REQUIRED_EVENT_NAME = "interrupt_required"
"""Interrupt required event indicating user action is needed."""

# MARK: - Assignment Events

ASSIGNMENT_RECEIVED_EVENT_NAME = "assignment_received"
"""Emitted when an assignment is received by an agent."""

ASSIGNMENT_COMPLETED_EVENT_NAME = "assignment_completed"
"""Emitted when an assignment is completed by an agent."""

# MARK: - Model Events

MODEL_TOOL_COMPLETE_EVENT_NAME = "model_tool_complete"
"""Emitted when a model tool call completes."""

# MARK: - Lifecycle Events

HEARTBEAT_EVENT_NAME = "heartbeat"
"""Periodic heartbeat event for connection health."""

UPDATE_EVENT_NAME = "update"
"""Progress update event during execution."""

PROGRESS_UPDATE_EVENT_NAME = "progress_update"
"""Progress update event for streamed response content during execution."""

STATUS_MESSAGE_EVENT_NAME = "status_message"
"""Standalone status message emitted at swarm lifecycle milestones.

Unlike ``progress_update`` (which carries streaming deltas that accumulate
into a single response), a ``status_message`` is a self-contained,
human-readable notification (e.g. "Dispatching 3 agents: ...").  Clients
should display each one as its own UI element rather than appending to
the assistant response stream.

Payload: ``{"message": str, "assistant_id": str}``
"""

FINAL_EVENT_NAME = "final"
"""Final event indicating execution completion."""

ERROR_EVENT_NAME = "error"
"""Error event indicating execution failure."""

# MARK: - System Tool Events

SYSTEM_TOOL_START_EVENT_NAME = "system_tool_start"
"""Emitted when a system tool (web_search, repl, think) starts execution."""

SYSTEM_TOOL_CHUNK_EVENT_NAME = "system_tool_chunk"
"""Emitted when a system tool produces a streaming chunk during execution."""

SYSTEM_TOOL_COMPLETE_EVENT_NAME = "system_tool_complete"
"""Emitted when a system tool completes execution."""

SYSTEM_TOOL_ERROR_EVENT_NAME = "system_tool_error"
"""Emitted when a system tool encounters an error."""

# MARK: - Hook Events

HOOK_FIRED_EVENT_NAME = "hook_fired"
"""Emitted each time a developer-registered scope or tool hook callback fires.

Carries the hook's scope ({tool, agent, swarm}), the firing stage
(``"before"`` / ``"after"``), the callable's display name, and either
``"completed"`` or ``"failed"`` plus an optional error message. The SDK
emits one event per hook execution so multiple hooks on the same target
each surface their own marker in the UI.
"""

# MARK: - Enrichment Events

ENRICHMENT_EVENT_NAME = "enrichment"
"""Emitted when an agent transitions to a new execution phase (evaluating, planning, etc.)."""

MEMORY_SUMMARIZING_ENRICHMENT_PHASE = "memory_summarizing"
"""Enrichment phase emitted before memory summarize-mode execution."""

MEMORY_SUMMARIZED_ENRICHMENT_PHASE = "memory_summarized"
"""Enrichment phase emitted after memory summarize-mode execution completes."""

MEMORY_RETRIEVING_ENRICHMENT_PHASE = "memory_retrieving"
"""Enrichment phase emitted before memory retrieve-mode execution."""

MEMORY_RETRIEVED_ENRICHMENT_PHASE = "memory_retrieved"
"""Enrichment phase emitted after memory retrieval completes."""

MEMORY_INDEXING_ENRICHMENT_PHASE = "memory_indexing"
"""Enrichment phase emitted before memory index-mode execution."""

MEMORY_INDEXED_ENRICHMENT_PHASE = "memory_indexed"
"""Enrichment phase emitted after memory index-mode execution completes."""

MEMORY_GRAPH_EXTRACTING_ENRICHMENT_PHASE = "memory_graph_extracting"
"""Enrichment phase emitted before graph/entity extraction in index-mode."""

MEMORY_SKILL_EXTRACTING_ENRICHMENT_PHASE = "memory_skill_extracting"
"""Enrichment phase emitted while post-run skill extraction is in progress."""

MEMORY_INSIGHT_EXTRACTING_ENRICHMENT_PHASE = "memory_insight_extracting"
"""Enrichment phase emitted while post-run insight extraction is in progress."""

MEMORY_SKILL_EXTRACTED_ENRICHMENT_PHASE = "memory_skill_extracted"
"""Enrichment phase emitted after post-run skill extraction completes."""

MEMORY_INSIGHT_EXTRACTED_ENRICHMENT_PHASE = "memory_insight_extracted"
"""Enrichment phase emitted after post-run insight extraction completes."""

MEMORY_ENRICHMENT_PHASES = (
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
"""Canonical memory-related enrichment phase identifiers."""

REDACTION_PREVIEWED_ENRICHMENT_PHASE = "redaction_previewed"
"""Enrichment phase emitted when an explicit redaction preview completes."""

MESSAGE_REDACTION_APPLIED_ENRICHMENT_PHASE = "message_redaction_applied"
"""Enrichment phase emitted when message redaction is applied during normal execution setup."""

REDACTION_ENRICHMENT_PHASES = (
    REDACTION_PREVIEWED_ENRICHMENT_PHASE,
    MESSAGE_REDACTION_APPLIED_ENRICHMENT_PHASE,
)
"""Canonical redaction-related enrichment phase identifiers."""

RESOURCE_REGISTERING_ENRICHMENT_PHASE = "resource_registering"
"""Enrichment phase emitted when resource registration begins."""

RESOURCE_REGISTERED_ENRICHMENT_PHASE = "resource_registered"
"""Enrichment phase emitted when resource registration completes."""

RESOURCE_DEDUP_REUSED_ENRICHMENT_PHASE = "resource_dedup_reused"
"""Enrichment phase emitted when existing resource content is reused (dedup)."""

RESOURCE_VERSION_SUPERSEDED_ENRICHMENT_PHASE = "resource_version_superseded"
"""Enrichment phase emitted when a previous resource version is superseded."""

RESOURCE_EXTRACTING_ENRICHMENT_PHASE = "resource_extracting"
"""Enrichment phase emitted when resource extraction starts."""

RESOURCE_EXTRACTED_ENRICHMENT_PHASE = "resource_extracted"
"""Enrichment phase emitted when resource extraction completes."""

RESOURCE_ENRICHMENT_PHASES = (
    RESOURCE_REGISTERING_ENRICHMENT_PHASE,
    RESOURCE_REGISTERED_ENRICHMENT_PHASE,
    RESOURCE_DEDUP_REUSED_ENRICHMENT_PHASE,
    RESOURCE_VERSION_SUPERSEDED_ENRICHMENT_PHASE,
    RESOURCE_EXTRACTING_ENRICHMENT_PHASE,
    RESOURCE_EXTRACTED_ENRICHMENT_PHASE,
)
"""Canonical resource-related enrichment phase identifiers."""

__all__ = [
    # Tool Events
    "TOOL_EVENT_NAME",
    "INTERRUPT_REQUEST_EVENT_NAME",
    "INTERRUPT_REQUIRED_EVENT_NAME",
    # Assignment Events
    "ASSIGNMENT_RECEIVED_EVENT_NAME",
    "ASSIGNMENT_COMPLETED_EVENT_NAME",
    # Model Events
    "MODEL_TOOL_COMPLETE_EVENT_NAME",
    # Lifecycle Events
    "HEARTBEAT_EVENT_NAME",
    "UPDATE_EVENT_NAME",
    "PROGRESS_UPDATE_EVENT_NAME",
    "STATUS_MESSAGE_EVENT_NAME",
    "FINAL_EVENT_NAME",
    "ERROR_EVENT_NAME",
    # System Tool Events
    "SYSTEM_TOOL_START_EVENT_NAME",
    "SYSTEM_TOOL_CHUNK_EVENT_NAME",
    "SYSTEM_TOOL_COMPLETE_EVENT_NAME",
    "SYSTEM_TOOL_ERROR_EVENT_NAME",
    # Hook Events
    "HOOK_FIRED_EVENT_NAME",
    # Enrichment Events
    "ENRICHMENT_EVENT_NAME",
    "MEMORY_SUMMARIZING_ENRICHMENT_PHASE",
    "MEMORY_SUMMARIZED_ENRICHMENT_PHASE",
    "MEMORY_RETRIEVING_ENRICHMENT_PHASE",
    "MEMORY_RETRIEVED_ENRICHMENT_PHASE",
    "MEMORY_INDEXING_ENRICHMENT_PHASE",
    "MEMORY_INDEXED_ENRICHMENT_PHASE",
    "MEMORY_GRAPH_EXTRACTING_ENRICHMENT_PHASE",
    "MEMORY_SKILL_EXTRACTING_ENRICHMENT_PHASE",
    "MEMORY_INSIGHT_EXTRACTING_ENRICHMENT_PHASE",
    "MEMORY_SKILL_EXTRACTED_ENRICHMENT_PHASE",
    "MEMORY_INSIGHT_EXTRACTED_ENRICHMENT_PHASE",
    "MEMORY_ENRICHMENT_PHASES",
    "REDACTION_PREVIEWED_ENRICHMENT_PHASE",
    "MESSAGE_REDACTION_APPLIED_ENRICHMENT_PHASE",
    "REDACTION_ENRICHMENT_PHASES",
    "RESOURCE_REGISTERING_ENRICHMENT_PHASE",
    "RESOURCE_REGISTERED_ENRICHMENT_PHASE",
    "RESOURCE_DEDUP_REUSED_ENRICHMENT_PHASE",
    "RESOURCE_VERSION_SUPERSEDED_ENRICHMENT_PHASE",
    "RESOURCE_EXTRACTING_ENRICHMENT_PHASE",
    "RESOURCE_EXTRACTED_ENRICHMENT_PHASE",
    "RESOURCE_ENRICHMENT_PHASES",
]
