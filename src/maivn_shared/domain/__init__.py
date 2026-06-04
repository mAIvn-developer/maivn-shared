# pyright: strict
"""Domain layer exports for maivn-shared."""

from __future__ import annotations

from typing import Protocol, cast

# MARK: - Entities
from .entities.memory_config import (
    MemoryConfig,
    MemoryInsightExtractionConfig,
    MemoryLevel,
    MemoryPersistenceMode,
    MemoryRetrievalConfig,
    MemorySharingScope,
    MemorySkillExtractionConfig,
)
from .entities.session import (
    RedactionPreviewRequest,
    RedactionPreviewResponse,
    SessionRequest,
    SessionResponse,
    SessionStartupResponse,
)
from .entities.session_config import (
    FinalOutputMode,
    MemoryAssetsConfig,
    MemoryResourceConfig,
    MemorySkillConfig,
    NestedSynthesisMode,
    OrchestrationMode,
    SessionExecutionConfig,
    SessionOrchestrationConfig,
    StopStrategy,
    StructuredOutputConfig,
    SwarmAgentConfig,
    SwarmConfig,
    SystemToolsConfig,
)
from .entities.session_config import (
    apply_session_configs_to_metadata as _apply_session_configs_to_metadata,
)
from .entities.tool_execution import ToolCall, ToolExecutionResult
from .entities.tool_spec import ToolSpec, ToolType

# MARK: - Exceptions
from .exceptions import (
    ConfigurationError,
    MaivnError,
    SerializationError,
    ValidationError,
    is_retryable,
    wrap_exception,
)

# MARK: - Types


class _ApplySessionConfigsToMetadata(Protocol):
    def __call__(
        self,
        metadata: dict[str, object],
        *,
        execution_config: SessionExecutionConfig | None = None,
        system_tools_config: SystemToolsConfig | None = None,
        structured_output_config: StructuredOutputConfig | None = None,
        orchestration_config: SessionOrchestrationConfig | None = None,
        memory_assets_config: MemoryAssetsConfig | None = None,
        swarm_config: SwarmConfig | None = None,
    ) -> None: ...


# MARK: - Public API

apply_session_configs_to_metadata = cast(
    _ApplySessionConfigsToMetadata,
    _apply_session_configs_to_metadata,
)

__all__ = [
    # MARK: - Entities
    "MemoryConfig",
    "MemoryAssetsConfig",
    "MemoryInsightExtractionConfig",
    "MemoryLevel",
    "MemoryPersistenceMode",
    "MemoryResourceConfig",
    "MemoryRetrievalConfig",
    "MemorySharingScope",
    "MemorySkillConfig",
    "MemorySkillExtractionConfig",
    "NestedSynthesisMode",
    "FinalOutputMode",
    "OrchestrationMode",
    "RedactionPreviewRequest",
    "RedactionPreviewResponse",
    "SessionExecutionConfig",
    "SessionOrchestrationConfig",
    "StopStrategy",
    "SessionRequest",
    "SessionResponse",
    "SessionStartupResponse",
    "StructuredOutputConfig",
    "SwarmAgentConfig",
    "SwarmConfig",
    "SystemToolsConfig",
    "apply_session_configs_to_metadata",
    "ToolCall",
    "ToolExecutionResult",
    "ToolSpec",
    "ToolType",
    # MARK: - Exceptions
    "ConfigurationError",
    "MaivnError",
    "SerializationError",
    "ValidationError",
    "is_retryable",
    "wrap_exception",
]
