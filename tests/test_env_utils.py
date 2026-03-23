from __future__ import annotations

from typing import Any

from maivn_shared.utils.env import get_env_float, get_env_int


class _Logger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def warning(self, message: str, *args: Any, **_kwargs: Any) -> None:
        rendered = message % args if args else message
        self.messages.append(rendered)


def test_get_env_float_uses_default_without_warning_for_empty_value() -> None:
    logger = _Logger()

    result = get_env_float("TEST_FLOAT", 3.5, {"TEST_FLOAT": ""}, logger=logger)

    assert result == 3.5
    assert logger.messages == []


def test_get_env_float_warns_for_invalid_non_empty_value() -> None:
    logger = _Logger()

    result = get_env_float("TEST_FLOAT", 3.5, {"TEST_FLOAT": "abc"}, logger=logger)

    assert result == 3.5
    assert logger.messages == ["Invalid float for TEST_FLOAT=abc. Using default 3.5."]


def test_get_env_int_uses_default_without_warning_for_empty_value() -> None:
    logger = _Logger()

    result = get_env_int("TEST_INT", 7, {"TEST_INT": ""}, logger=logger)

    assert result == 7
    assert logger.messages == []


def test_get_env_int_warns_for_invalid_non_empty_value() -> None:
    logger = _Logger()

    result = get_env_int("TEST_INT", 7, {"TEST_INT": "abc"}, logger=logger)

    assert result == 7
    assert logger.messages == ["Invalid int for TEST_INT=abc. Using default 7."]
