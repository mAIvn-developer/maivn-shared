"""Structured-metrics logging methods for :class:`MaivnLogger`.

Token-usage and tool-execution metrics are emitted as structured log
entries — file-only for token usage, console+file for tool execution —
keyed by stable component names so log consumers can grep / aggregate.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from .config import LogLevel


# MARK: MaivnLoggerMetricsMixin


class MaivnLoggerMetricsMixin:
    """Structured emission for token-usage and tool-execution metrics.

    Assumes the concrete class provides ``_writer`` and
    ``_write_structured_log``.
    """

    # MARK: - Token Usage

    def log_token_usage(
        self,
        agent_name: str,
        invocation_type: str,
        total_tokens: int,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
        model: str = "unknown",
        provider: str = "unknown",
        total_cost: float = 0.0,
        session_id: str | None = None,
        thread_id: str | None = None,
        batch_number: int | None = None,
        **metadata: Any,
    ) -> None:
        """Emit a structured token-usage record (file only; never console)."""
        if not self._writer.file_logging_enabled:  # type: ignore[attr-defined]
            return

        cache_hit_rate = (cache_read_tokens / input_tokens * 100) if input_tokens > 0 else 0
        non_cached_input = input_tokens - cache_read_tokens

        data: dict[str, Any] = {
            "agent_name": agent_name,
            "invocation_type": invocation_type,
            "model": model,
            "provider": provider,
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_tokens": cache_read_tokens,
            "cache_creation_tokens": cache_creation_tokens,
            "non_cached_input_tokens": non_cached_input,
            "cache_hit_rate_pct": round(cache_hit_rate, 1),
            "total_cost_usd": round(total_cost, 6),
        }

        if session_id:
            data["session_id"] = session_id
        if thread_id:
            data["thread_id"] = thread_id
        if batch_number is not None:
            data["batch_number"] = batch_number

        data.update(metadata)

        self._write_structured_log(  # type: ignore[attr-defined]
            level="INFO",
            component="TOKEN_USAGE",
            event="token_usage",
            data=data,
        )

    # MARK: - Tool Execution

    def log_tool_execution(
        self,
        phase: Literal["start", "completed", "failed"],
        tool_id: str,
        tool_name: str,
        tool_type: str | None = None,
        args: dict[str, Any] | None = None,
        result: Any = None,
        error: str | None = None,
        elapsed_ms: int | None = None,
        session_id: str | None = None,
        thread_id: str | None = None,
        task_idx: int | None = None,
        **metadata: Any,
    ) -> None:
        """Emit a structured tool-execution record covering one lifecycle phase.

        ``phase`` is one of ``"start"`` / ``"completed"`` / ``"failed"``;
        the third drives ``level="ERROR"``. ``args`` is summarized to keys
        only (raw values are never logged) and ``result`` is truncated to
        a 200-char preview.
        """
        level: LogLevel = "ERROR" if phase == "failed" else "INFO"

        data: dict[str, Any] = {
            "tool_id": tool_id,
            "tool_name": tool_name,
            "tool_type": tool_type,
            "phase": phase,
            "elapsed_ms": elapsed_ms,
        }

        if session_id:
            data["session_id"] = session_id
        if thread_id:
            data["thread_id"] = thread_id
        if task_idx is not None:
            data["task_idx"] = task_idx
        if args:
            data["args_keys"] = list(args.keys())
        if result is not None:
            result_str = str(result)
            data["result_preview"] = result_str[:200] if len(result_str) > 200 else result_str
        if error:
            data["error"] = error

        data.update(metadata)

        self._write_structured_log(  # type: ignore[attr-defined]
            level=level,
            component="TOOL_EXECUTION",
            event=f"tool_{phase}",
            data=data,
        )


__all__ = ["MaivnLoggerMetricsMixin"]
