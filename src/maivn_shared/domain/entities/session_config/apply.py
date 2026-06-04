# pyright: strict
"""Projection of typed session configs into legacy runtime metadata."""

from __future__ import annotations

from ._helpers import JsonObject
from .execution import SessionExecutionConfig
from .memory_assets import MemoryAssetsConfig
from .orchestration import SessionOrchestrationConfig
from .structured_output import StructuredOutputConfig
from .swarm import SwarmConfig
from .system_tools import SystemToolsConfig

# MARK: Metadata Projection


def apply_session_configs_to_metadata(
    metadata: JsonObject,
    *,
    execution_config: SessionExecutionConfig | None = None,
    system_tools_config: SystemToolsConfig | None = None,
    structured_output_config: StructuredOutputConfig | None = None,
    orchestration_config: SessionOrchestrationConfig | None = None,
    memory_assets_config: MemoryAssetsConfig | None = None,
    swarm_config: SwarmConfig | None = None,
) -> None:
    """Project typed session configs into legacy runtime metadata."""
    if execution_config is not None and execution_config.is_configured():
        metadata.update(execution_config.to_metadata_patch())
    if system_tools_config is not None and system_tools_config.is_configured():
        metadata.update(system_tools_config.to_metadata_patch())
    if structured_output_config is not None and structured_output_config.is_configured():
        metadata.update(structured_output_config.to_metadata_patch())
    if orchestration_config is not None and orchestration_config.is_configured():
        metadata.update(orchestration_config.to_metadata_patch())
    if memory_assets_config is not None and memory_assets_config.is_configured():
        metadata.update(memory_assets_config.to_metadata_patch())
    if swarm_config is not None and swarm_config.is_configured():
        metadata.update(swarm_config.to_metadata_patch())


__all__ = ["apply_session_configs_to_metadata"]
