# pyright: strict
"""Tests for token-usage metric emission (shared-core-infra-9).

The ``cache_hit_rate_pct`` field must always be a float so downstream
strict JSON parsers see a stable numeric type, including the
divide-by-zero branch where ``input_tokens == 0``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typing_extensions import override

from maivn_shared.infrastructure.logging import MaivnLogger
from maivn_shared.infrastructure.logging.config import LogLevel
from maivn_shared.utils.redaction import REDACTED

# MARK: - Capturing subclass


class _CapturingLogger(MaivnLogger):
    """MaivnLogger that captures the structured data of token-usage records."""

    token_usage_data: dict[str, object]

    @override
    def __init__(self, log_file_path: Path | str | None) -> None:
        self.token_usage_data = {}
        super().__init__(
            log_file_path=log_file_path,
            console_level="OFF",
            file_level="INFO",
            human_readable_console=False,
            use_colors=False,
        )

    @override
    def _write_structured_log(
        self,
        level: LogLevel,
        component: str,
        event: str,
        data: dict[str, object],
    ) -> None:
        if component == "TOKEN_USAGE":
            self.token_usage_data = dict(data)
        super()._write_structured_log(level, component, event, data)


def _capture_token_usage(
    tmp_path: Path, *, input_tokens: int, cache_read: int
) -> dict[str, object]:
    """Emit one token-usage record and return the structured data dict it built."""
    logger = _CapturingLogger(tmp_path / "tokens.log")
    logger.log_token_usage(
        agent_name="planner",
        invocation_type="plan",
        total_tokens=input_tokens + 10,
        input_tokens=input_tokens,
        output_tokens=10,
        cache_read_tokens=cache_read,
    )
    return logger.token_usage_data


# MARK: - shared-core-infra-9: cache_hit_rate_pct is always float


def test_cache_hit_rate_is_float_in_zero_branch(tmp_path: Path) -> None:
    """Zero input tokens -> cache_hit_rate_pct must be 0.0 (float), not int 0."""
    data = _capture_token_usage(tmp_path, input_tokens=0, cache_read=0)
    rate = data["cache_hit_rate_pct"]
    assert rate == 0.0
    assert isinstance(rate, float)
    assert not isinstance(rate, bool)


def test_cache_hit_rate_is_float_in_nonzero_branch(tmp_path: Path) -> None:
    """Non-zero input keeps cache_hit_rate_pct a float (consistency check)."""
    data = _capture_token_usage(tmp_path, input_tokens=100, cache_read=50)
    rate = data["cache_hit_rate_pct"]
    assert rate == 50.0
    assert isinstance(rate, float)


def test_cache_hit_rate_pct_is_json_type_stable(tmp_path: Path) -> None:
    """Both branches serialize cache_hit_rate_pct with a JSON float literal."""
    zero = _capture_token_usage(tmp_path, input_tokens=0, cache_read=0)
    nonzero = _capture_token_usage(tmp_path, input_tokens=100, cache_read=50)
    zero_text = json.dumps({"r": zero["cache_hit_rate_pct"]})
    nonzero_text = json.dumps({"r": nonzero["cache_hit_rate_pct"]})
    # A JSON float literal carries a decimal point; an int literal would not.
    assert zero_text == '{"r": 0.0}'
    assert nonzero_text == '{"r": 50.0}'


def test_tool_execution_redacts_context_metadata_and_default_result_preview(
    capsys: pytest.CaptureFixture[str],
) -> None:
    logger = MaivnLogger(console_level="INFO", human_readable_console=False, use_colors=False)
    logger.set_context(access_token="context-secret")
    logger.log_custom("INFO", "TEST", "event", api_key="metadata-secret")
    logger.log_tool_execution(
        phase="completed",
        tool_id="tool-1",
        tool_name="lookup",
        result={"token": "result-secret"},
    )

    output = capsys.readouterr().out

    assert "context-secret" not in output
    assert "metadata-secret" not in output
    assert "result-secret" not in output
    assert REDACTED in output
