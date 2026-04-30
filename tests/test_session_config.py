from __future__ import annotations

import pytest
from pydantic import ValidationError

from maivn_shared.domain.entities.session_config import (
    SwarmAgentConfig,
    SwarmConfig,
    normalize_nested_synthesis,
)


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (None, None),
        (True, True),
        (False, False),
        ("auto", "auto"),
        (" Auto ", "auto"),
        ("true", True),
        ("YES", True),
        ("0", False),
        ("off", False),
    ],
)
def test_normalize_nested_synthesis_accepts_supported_modes(
    raw_value: object,
    expected: bool | str | None,
) -> None:
    assert normalize_nested_synthesis(raw_value) == expected


@pytest.mark.parametrize("raw_value", [1, 0, object(), "sometimes", ["auto"]])
def test_normalize_nested_synthesis_rejects_unsupported_modes(raw_value: object) -> None:
    with pytest.raises(ValueError, match="included_nested_synthesis"):
        normalize_nested_synthesis(raw_value)


@pytest.mark.parametrize("model_type", [SwarmAgentConfig, SwarmConfig])
def test_nested_synthesis_config_models_reject_unsupported_modes(
    model_type: type[SwarmAgentConfig] | type[SwarmConfig],
) -> None:
    with pytest.raises(ValidationError):
        model_type.model_validate({"included_nested_synthesis": 1})
