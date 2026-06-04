# pyright: strict
from __future__ import annotations

import pytest

from maivn_shared.utils.env import get_env_bool, get_env_float, get_env_int

# MARK: Helpers


class _Logger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def warning(self, message: str, *args: object, **_kwargs: object) -> None:
        rendered = message % args if args else message
        self.messages.append(rendered)


# MARK: Tests


def test_get_env_float_uses_default_without_warning_for_empty_value() -> None:
    logger = _Logger()

    result = get_env_float("TEST_FLOAT", 3.5, {"TEST_FLOAT": ""}, logger=logger)

    assert result == 3.5
    assert logger.messages == []


def test_get_env_float_warns_for_invalid_non_empty_value() -> None:
    logger = _Logger()

    result = get_env_float("TEST_FLOAT", 3.5, {"TEST_FLOAT": "secret-rate"}, logger=logger)

    assert result == 3.5
    assert logger.messages == ["Invalid float for TEST_FLOAT. Using default 3.5."]
    assert "secret-rate" not in repr(logger.messages)


def test_get_env_int_uses_default_without_warning_for_empty_value() -> None:
    logger = _Logger()

    result = get_env_int("TEST_INT", 7, {"TEST_INT": ""}, logger=logger)

    assert result == 7
    assert logger.messages == []


def test_get_env_int_warns_for_invalid_non_empty_value() -> None:
    logger = _Logger()

    result = get_env_int("TEST_INT", 7, {"TEST_INT": "secret-port"}, logger=logger)

    assert result == 7
    assert logger.messages == ["Invalid int for TEST_INT. Using default 7."]
    assert "secret-port" not in repr(logger.messages)


# MARK: get_env_bool


@pytest.mark.parametrize(
    "raw",
    [
        "0",
        "false",
        "False",
        "FALSE",
        "FaLsE",
        "no",
        "No",
        "NO",
        "nO",
        "off",
        "Off",
        "OFF",
        "",
        # Surrounding whitespace must not flip a falsy value to True.
        "false ",
        " false",
        "  False  ",
        "\tno\n",
        " off ",
    ],
)
def test_get_env_bool_falsy_values_are_case_and_whitespace_insensitive(raw: str) -> None:
    assert get_env_bool("FLAG", True, {"FLAG": raw}) is False


@pytest.mark.parametrize(
    "raw",
    ["1", "true", "True", "yes", "on", "enabled", " 1 ", "anything"],
)
def test_get_env_bool_non_falsy_values_are_true(raw: str) -> None:
    assert get_env_bool("FLAG", False, {"FLAG": raw}) is True


def test_get_env_bool_missing_uses_default() -> None:
    assert get_env_bool("MISSING", True, {}) is True
    assert get_env_bool("MISSING", False, {}) is False
