# pyright: strict
"""Tests for logging config env parsing (shared-core-infra-8).

The log-level env parser must only ever yield a value drawn from the
``LogLevel`` literal: a valid env value passes through (upper-cased),
anything else falls back to the documented default. Exercised through the
public module constants via a controlled reload so no module-private
symbol is imported.
"""

from __future__ import annotations

import importlib
from typing import cast

import pytest

import maivn_shared.infrastructure.logging.config as config_module

# MARK: - Helpers

_VALID_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF"})


def _reload_console_level(monkeypatch: pytest.MonkeyPatch, raw: str | None) -> str:
    """Reload the config module with MAIVN_LOG_LEVEL set to ``raw`` and return the default."""
    if raw is None:
        monkeypatch.delenv("MAIVN_LOG_LEVEL", raising=False)
    else:
        monkeypatch.setenv("MAIVN_LOG_LEVEL", raw)
    reloaded = importlib.reload(config_module)
    try:
        return cast(str, reloaded.DEFAULT_CONSOLE_LEVEL)
    finally:
        # Restore the canonical (env-free) module so later tests see defaults.
        monkeypatch.delenv("MAIVN_LOG_LEVEL", raising=False)
        _ = importlib.reload(config_module)


# MARK: - shared-core-infra-8: env value is validated/narrowed


def test_valid_env_value_passes_through(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _reload_console_level(monkeypatch, "warning") == "WARNING"


def test_invalid_env_value_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    # MAIVN_LOG_LEVEL documented default is OFF.
    assert _reload_console_level(monkeypatch, "NOT_A_LEVEL") == "OFF"


def test_unset_env_value_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _reload_console_level(monkeypatch, None) == "OFF"


def test_result_is_always_a_valid_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """Whatever the env holds, the derived level is a member of the LogLevel set."""
    for raw in ("", "info", "garbage", "OFF", "Critical"):
        assert _reload_console_level(monkeypatch, raw) in _VALID_LEVELS
