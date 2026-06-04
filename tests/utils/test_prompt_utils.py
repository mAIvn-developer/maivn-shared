# pyright: strict
from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from maivn_shared.utils.prompt_utils import load_prompt, load_prompt_text

# MARK: Fixtures


@pytest.fixture(autouse=True)
def clear_prompt_cache() -> Iterator[None]:
    """Reset the prompt-text cache so cached content never leaks between tests."""
    load_prompt_text.cache_clear()
    yield
    load_prompt_text.cache_clear()


@pytest.fixture
def prompt_package(tmp_path: Path) -> Iterator[str]:
    """Create an importable package on disk holding a single prompt file.

    Yields the package name; the parent dir is on ``sys.path`` for the test only.
    """
    package_name = "tmp_prompt_pkg"
    pkg_dir = tmp_path / package_name
    pkg_dir.mkdir()
    _ = (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
    _ = (pkg_dir / "SAMPLE.md").write_text("Hello $name", encoding="utf-8")

    sys.path.insert(0, str(tmp_path))
    importlib.invalidate_caches()
    try:
        yield package_name
    finally:
        sys.path.remove(str(tmp_path))
        _ = sys.modules.pop(package_name, None)


# MARK: Tests


@pytest.mark.parametrize(
    "filename",
    [
        "../secret",
        "prompts/../../secret",
        "C:/secret",
        "prompts//secret",
        "/absolute/prompt",
        "",
    ],
)
def test_load_prompt_rejects_non_plain_prompt_filenames(filename: str) -> None:
    with pytest.raises(ValueError, match="Prompt filename must be a plain Markdown file name"):
        _ = load_prompt(filename, "maivn_shared.utils")


def test_load_prompt_accepts_package_relative_subpaths(prompt_package: str, tmp_path: Path) -> None:
    nested = tmp_path / prompt_package / "nested"
    nested.mkdir()
    _ = (nested / "NESTED.md").write_text("Nested $name", encoding="utf-8")

    result = load_prompt("nested/NESTED", prompt_package, name="ok")

    assert result == "Nested ok"


def test_load_prompt_returns_identical_content_on_repeat(prompt_package: str) -> None:
    first = load_prompt("SAMPLE.md", prompt_package, name="world")
    second = load_prompt("SAMPLE.md", prompt_package, name="world")

    assert first == "Hello world"
    assert second == first


def test_load_prompt_caches_text_across_calls(prompt_package: str, tmp_path: Path) -> None:
    """shared-utils-6: the text-load step is cached, so on-disk edits are not re-read.

    This documents the accepted tradeoff: prompt-file hot-reload is disabled until
    the process restarts (or the cache is cleared).
    """
    first = load_prompt("SAMPLE.md", prompt_package)

    # Mutate the underlying file; a non-cached loader would pick this up.
    _ = (tmp_path / prompt_package / "SAMPLE.md").write_text("Changed $name", encoding="utf-8")
    second = load_prompt("SAMPLE.md", prompt_package)

    assert first == "Hello $name"
    assert second == first  # cached: the on-disk change is intentionally not observed

    # After clearing the cache the new content is observed.
    load_prompt_text.cache_clear()
    third = load_prompt("SAMPLE.md", prompt_package)
    assert third == "Changed $name"
