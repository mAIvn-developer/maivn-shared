# pyright: strict
"""Regression + equivalence tests for the MaivnLogger write path.

Covers the P6-SH-B findings:
- shared-core-infra-1: disabled-level calls skip payload sanitization.
- shared-core-infra-7: a long message is truncated exactly once (snapshot).
"""

from __future__ import annotations

from pathlib import Path

from typing_extensions import override

from maivn_shared.infrastructure.logging.maivn_logger import MaivnLogger

# MARK: - Recording subclass


class _RecordingLogger(MaivnLogger):
    """MaivnLogger that counts sanitizer calls and exposes a deterministic flush.

    Subclassing keeps the protected-member access inside the class hierarchy,
    so the test stays type-clean while observing the hot-path guard.
    """

    sanitize_calls: int

    @override
    def __init__(self, log_file_path: Path | str | None = None) -> None:
        self.sanitize_calls = 0
        super().__init__(
            log_file_path=log_file_path,
            console_level="OFF",
            file_level="INFO",
            use_colors=False,
        )

    @override
    def _sanitize_mapping(self, data: dict[str, object]) -> dict[str, object]:
        self.sanitize_calls += 1
        return super()._sanitize_mapping(data)

    def flush(self) -> None:
        """Drain the background file-writer thread so file assertions are stable."""
        self._writer.close()


# MARK: - shared-core-infra-1: disabled-level short-circuits sanitization


def test_disabled_level_skips_sanitization() -> None:
    """A fully-disabled level must not run payload sanitization (HIGH perf fix)."""
    # console OFF and no file logging -> DEBUG is disabled on both sinks.
    logger = _RecordingLogger()
    baseline = logger.sanitize_calls  # startup banner already sanitized once.

    logger.debug("disabled message %s", "arg", component="APP", secret="should-not-be-walked")

    assert logger.sanitize_calls == baseline, "sanitization ran for a disabled-level call"


def test_enabled_level_still_sanitizes(tmp_path: Path) -> None:
    """An enabled level must still run sanitization (guard is not over-broad)."""
    logger = _RecordingLogger(tmp_path / "maivn.log")
    baseline = logger.sanitize_calls

    logger.info("enabled message", component="APP", key="value")
    logger.flush()

    assert logger.sanitize_calls > baseline, "sanitization did not run for an enabled-level call"


# MARK: - shared-core-infra-7: single truncation boundary (snapshot)


def test_long_message_truncated_once_to_max_length(tmp_path: Path) -> None:
    """A long message lands clamped to max_message_length exactly once."""
    logger = _RecordingLogger(tmp_path / "maivn.log")
    log_file = tmp_path / "maivn.log"

    logger.warning("A" * 1000, component="APP")
    logger.flush()

    contents = log_file.read_text(encoding="utf-8")
    # The rendered message is clamped to 400 (default) with a "..." suffix marker.
    assert "A" * 397 + "..." in contents
    # Never the full 1000-char message.
    assert "A" * 401 not in contents


def test_long_message_snapshot_stable_across_repeated_calls(tmp_path: Path) -> None:
    """The truncated file line is deterministic for a fixed long message."""
    logger = _RecordingLogger(tmp_path / "maivn.log")
    log_file = tmp_path / "maivn.log"

    logger.warning("B" * 1000, component="APP")
    logger.warning("B" * 1000, component="APP")
    logger.flush()

    lines = [ln for ln in log_file.read_text(encoding="utf-8").splitlines() if "[WARNING]" in ln]
    assert len(lines) == 2
    # Both lines carry an identical message body (timestamp differs, body does not).
    body0 = lines[0].split("[APP]", 1)[1]
    body1 = lines[1].split("[APP]", 1)[1]
    assert body0 == body1
