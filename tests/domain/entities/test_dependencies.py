# pyright: strict
from __future__ import annotations

import pytest
from pydantic import ValidationError

from maivn_shared.domain.entities.dependencies import InterruptDependency

# MARK: Helpers


def _handle_input(value: str) -> str:
    return value


# MARK: Tests


def test_interrupt_dependency_allows_text_without_choices() -> None:
    dependency = InterruptDependency(
        name="input",
        arg_name="input",
        prompt="Enter value",
        input_handler=_handle_input,
        input_type="text",
    )

    assert dependency.choices == []


def test_interrupt_dependency_requires_choices_for_choice_input_type() -> None:
    with pytest.raises(
        ValidationError, match="choices must be provided when input_type is 'choice' or 'literal'"
    ):
        _ = InterruptDependency(
            name="input",
            arg_name="input",
            prompt="Select a value",
            input_handler=_handle_input,
            input_type="choice",
        )


def test_interrupt_dependency_accepts_choices_for_literal_input_type() -> None:
    dependency = InterruptDependency(
        name="input",
        arg_name="input",
        prompt="Select a value",
        input_handler=_handle_input,
        input_type="literal",
        choices=["a", "b"],
    )

    assert dependency.choices == ["a", "b"]


def test_interrupt_dependency_rejects_invalid_input_type() -> None:
    with pytest.raises(ValidationError, match="Input should be"):
        _ = InterruptDependency.model_validate(
            {
                "name": "input",
                "arg_name": "input",
                "prompt": "Select a value",
                "input_handler": _handle_input,
                "input_type": "invalid",
            }
        )
