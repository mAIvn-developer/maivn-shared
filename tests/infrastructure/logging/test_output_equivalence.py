# pyright: strict
"""Snapshot-equivalence checks for the MaivnLogger write path (prompt section 8).

These pin the rendered output for enabled levels so the P6-SH-B refactor
(early-return guard, single truncation boundary) stays byte-stable for the
message body. Timestamps vary per call, so the body after the
``[COMPONENT]`` marker is the stable subject.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from typing_extensions import override

from maivn_shared.infrastructure.logging.maivn_logger import MaivnLogger

# MARK: - Helpers

_TIMESTAMP_RE = re.compile(r"^\[[^\]]+\] ")


class _FlushableLogger(MaivnLogger):
    """File-backed logger exposing a deterministic flush for file assertions."""

    @override
    def __init__(self, log_file_path: Path | str) -> None:
        super().__init__(
            log_file_path=log_file_path,
            console_level="OFF",
            file_level="INFO",
            human_readable_console=False,
            use_colors=False,
        )

    def flush(self) -> None:
        self._writer.close()


def _console_bodies(captured: str) -> list[str]:
    """Return console lines (timestamp stripped), excluding the startup banner."""
    lines = [ln for ln in captured.splitlines() if ln.strip()]
    bodies = [_TIMESTAMP_RE.sub("", line, count=1) for line in lines]
    return [body for body in bodies if not body.startswith("[INFO] [SYSTEM]")]


def _file_bodies(log_file: Path) -> list[str]:
    """Return file lines (timestamp stripped), excluding the startup banner."""
    lines = log_file.read_text(encoding="utf-8").splitlines()
    bodies = [_TIMESTAMP_RE.sub("", line, count=1) for line in lines]
    return [body for body in bodies if not body.startswith("[INFO] [SYSTEM]")]


# MARK: - Enabled-level console output is stable


def test_info_console_output_is_stable(capsys: pytest.CaptureFixture[str]) -> None:
    logger = MaivnLogger(console_level="INFO", file_level="OFF", use_colors=False)
    logger.info("hello world", component="APP")

    bodies = _console_bodies(capsys.readouterr().out)
    assert bodies == ["[INFO] [APP] hello world"]


def test_long_warning_console_output_is_stable(capsys: pytest.CaptureFixture[str]) -> None:
    logger = MaivnLogger(console_level="INFO", file_level="OFF", use_colors=False)
    logger.warning("Z" * 1000, component="APP")

    bodies = _console_bodies(capsys.readouterr().out)
    # 400-char clamp with "..." marker: 397 chars + "..." = 400.
    assert bodies == [f"[WARNING] [APP] {'Z' * 397}..."]


# MARK: - Enabled-level file output is stable


def test_token_usage_file_output_is_stable(tmp_path: Path) -> None:
    logger = _FlushableLogger(tmp_path / "equiv.log")
    logger.log_token_usage(
        agent_name="planner",
        invocation_type="plan",
        total_tokens=110,
        input_tokens=0,
        output_tokens=10,
    )
    logger.flush()

    bodies = _file_bodies(tmp_path / "equiv.log")
    # File line renders the event fallback message (data has no "message" key).
    assert bodies == ["[INFO] [TOKEN_USAGE] token_usage event in TOKEN_USAGE"]
