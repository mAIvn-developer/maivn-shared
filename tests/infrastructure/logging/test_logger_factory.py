# pyright: strict
"""Tests for get_logger() global-instance management (shared-core-infra-2).

Concurrent first calls to ``get_logger()`` must return the same instance
(single writer thread), never racing to construct duplicate loggers.
"""

from __future__ import annotations

import threading

import pytest

from maivn_shared.infrastructure.logging import logger as logger_module
from maivn_shared.infrastructure.logging.logger import get_logger

# MARK: - shared-core-infra-2: thread-safe lazy global init


def test_get_logger_returns_same_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(logger_module, "_logger_instance", None)
    first = get_logger()
    second = get_logger()
    assert first is second


def test_concurrent_get_logger_returns_single_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Many threads racing the first call must observe one shared instance."""
    monkeypatch.setattr(logger_module, "_logger_instance", None)

    instances: list[object] = []
    barrier = threading.Barrier(16)

    def _worker() -> None:
        _ = barrier.wait()
        instances.append(get_logger())

    threads = [threading.Thread(target=_worker) for _ in range(16)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(instances) == 16
    assert len({id(instance) for instance in instances}) == 1
