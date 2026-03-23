"""Client-facing token usage model.

This module contains only the simple TokenUsage model for SDK consumers.
Service-specific models and normalization are in respective service packages.

## Model Hierarchy

This is the **client-facing** model exposed to SDK consumers. For internal
service models used by maivn infrastructure, see:

- **maivn-internal-shared** (`maivn_internal_shared.tokens.models`):
  - `DetailedTokenUsage`: Internal model with cost breakdown and execution context

- **maivn-agents** (`maivn_agents.infra.llm.pricing.usage`):
  - `TokenUsage`: Per-invocation dataclass with cost calculation
  - `UsageTracker`: Thread-safe aggregation across LLM calls

## Field Naming Conventions

All models use consistent field naming:
- `total_tokens`: Total tokens (input + output)
- `input_tokens`: Input/prompt tokens
- `output_tokens`: Output/completion tokens
- `cache_read_tokens`: Tokens read from cache
- `cache_creation_tokens`: Tokens written to cache

Note: Cost information is intentionally excluded from this public model.
Cost details are internal and only available via `DetailedTokenUsage`.
"""

from __future__ import annotations

from pydantic import BaseModel

# MARK: Client Model


class TokenUsage(BaseModel):
    """Token usage metrics - public SDK model.

    This model contains only token counts for SDK consumers.
    Cost information is intentionally excluded from the public API
    and is only available internally via `DetailedTokenUsage`.

    Attributes:
        total_tokens: Total number of tokens used.
        input_tokens: Number of input tokens used.
        output_tokens: Number of output tokens used.
        cache_read_tokens: Number of tokens read from cache.
        cache_creation_tokens: Number of tokens written to cache.
    """

    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    reasoning_tokens: int = 0
