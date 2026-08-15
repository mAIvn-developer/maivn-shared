# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.3] - 2026-08-14

### Added

- Added the provider-neutral `ultra` model tier to the shared session and
  scoped-model contracts.

## [0.4.2] - 2026-06-25

### Added

- Added and publicly exported the scoped model-selection contracts:
  `ModelChoice`, `ModelConfig`, `ModelConfigPart`, and `ModelTier`.

### Changed

- Expanded `SessionRequest.model` to accept either a provider-neutral tier or
  a scoped `ModelConfig`.
- Raised the minimum `langsmith` version to `0.8.18`.

## [0.4.1] - 2026-06-18

### Added

- Added the public `status_message_chunk` event for incremental status-card
  updates.
- Added `output_schema` and `schema_only` tool-spec contracts, including
  output-schema dependency discovery and serialization.

### Changed

- Tool specs now omit unset fields when serialized in a `SessionRequest`.
- Added the public developer-documentation URL to the package metadata.

## [0.4.0] - 2026-06-04

### Added

- Method-tool entity type and class-based toolset domain support, backing the SDK `@toolset` / `@toolify` / `agent.add_toolset()` API.

### Changed

- Strict-typing pass across the package (basedpyright strict; JSON-Schema-compliant entity serialization).
- CI: OSS license audit relaxed to `--frozen` (drops the lock-staleness gate).

## [0.3.0] - 2026-05-13

### Added

- Orchestration configuration options on the typed session entities.
- `swarm_has_final_tool` flag on `SwarmConfig`.
- "Hook fired" event support, with expanded documentation.

## [0.2.0] - 2026-05-01

### Added

- `invokes_via_dependency` field on `SwarmAgentConfig` to track agents auto-invoked via `@depends_on_agent` tool dependencies, letting orchestrators skip redundant stage scheduling.
- Typed session config entities: `SessionExecutionConfig`, `SessionOrchestrationConfig`, `StructuredOutputConfig`, `SwarmConfig`, `SystemToolsConfig`.
- Typed memory asset configs: `MemoryAssetsConfig`, `MemoryResourceConfig`, `MemorySkillConfig`, `NestedSynthesisMode`.
- `SessionRequest` now accepts typed config fields: `execution_config`, `system_tools_config`, `structured_output_config`, `orchestration_config`, `memory_assets_config`, `swarm_config`.
- PII whitelist support: `PIIWhitelist`, `PIIWhitelistEntry`, and `HIPAA_SAFE_HARBOR_CATEGORIES` entities.
- `RedactedMessage` accepts an optional `pii_whitelist` parameter; `SessionRequest` gains a session-level `pii_whitelist` field.
- `is_reserved` helper for session config validation.

### Changed

- `MaivnLogger.error()` mirrors `error_message` into the `message` field for clearer log output.
- Updated runtime dependencies and refreshed third-party license audit.

## [0.1.0] - Initial release

- Domain entities (tools, sessions, messages, dependencies).
- Core event name constants and shared infrastructure (logging, HTTP client, API endpoints).
