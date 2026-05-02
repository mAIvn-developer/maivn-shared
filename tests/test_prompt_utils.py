from __future__ import annotations

import pytest

from maivn_shared.utils.prompt_utils import load_prompt


@pytest.mark.parametrize(
    "filename",
    [
        "../secret",
        "prompts/../../secret",
        "/tmp/secret",
        "prompts//secret",
        "",
    ],
)
def test_load_prompt_rejects_non_package_local_paths(filename: str) -> None:
    with pytest.raises(ValueError):
        load_prompt(filename, "maivn_shared.utils")
