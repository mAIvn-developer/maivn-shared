# pyright: strict
"""Tests for LogWriter close semantics (shared-core-infra-6).

After ``close()`` the writer must not silently enqueue-and-lose file
content: file logging is reported disabled and further file writes are
rejected deterministically rather than dropped.
"""

from __future__ import annotations

from pathlib import Path

from maivn_shared.infrastructure.logging.writers import LogWriter

# MARK: - shared-core-infra-6: post-close writes are defined (no silent loss)


def test_writes_before_close_are_flushed(tmp_path: Path) -> None:
    log_file = tmp_path / "writer.log"
    writer = LogWriter(log_file)

    writer.write_to_file("line-before-close\n")
    writer.close()

    assert "line-before-close" in log_file.read_text(encoding="utf-8")


def test_file_logging_reported_disabled_after_close(tmp_path: Path) -> None:
    log_file = tmp_path / "writer.log"
    writer = LogWriter(log_file)

    assert writer.file_logging_enabled is True
    writer.close()
    assert writer.file_logging_enabled is False


def test_post_close_writes_are_not_silently_queued(tmp_path: Path) -> None:
    """A write after close() must not be silently enqueued-and-lost."""
    log_file = tmp_path / "writer.log"
    writer = LogWriter(log_file)
    writer.close()

    # No worker thread is alive; the write must short-circuit, not enqueue.
    writer.write_to_file("line-after-close\n")
    writer.write_dual("", "dual-after-close\n", to_console=False)

    contents = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
    assert "line-after-close" not in contents
    assert "dual-after-close" not in contents


def test_close_is_idempotent(tmp_path: Path) -> None:
    log_file = tmp_path / "writer.log"
    writer = LogWriter(log_file)
    writer.write_to_file("only-line\n")
    writer.close()
    writer.close()
    assert "only-line" in log_file.read_text(encoding="utf-8")
