# pyright: strict
"""Utilities for loading and formatting prompts from markdown files."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from functools import cache
from importlib import import_module
from importlib import resources as _resources
from importlib.resources import read_text as read_resource_text
from pathlib import Path
from string import Template

# MARK: - Constants

_logger = logging.getLogger(__name__)
_PROMPT_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9_.-]*$")


# MARK: - Public API


def load_prompt(filename: str, package_name: str, **kwargs: object) -> str:
    """Load a markdown prompt from a package's prompts directory.

    Args:
        filename: Name of the prompt file (with or without .md extension)
        package_name: Full package name where prompts are located
        **kwargs: Values to substitute in the prompt (use $var syntax)

    Returns:
        Formatted prompt text

    Example:
        >>> load_prompt('MY_PROMPT.md', 'maivn_shared.prompts', var1='value1')

    Use $var or ${var} syntax for variable substitution.
    """
    normalized_filename = _normalize_prompt_filename(filename)
    text = load_prompt_text(normalized_filename, package_name)
    return render_prompt(text, kwargs=kwargs)


def render_prompt(
    text: str,
    kwargs: Mapping[str, object] | None = None,
    **extra_kwargs: object,
) -> str:
    """Format prompt text using Template for safe substitution.

    Args:
        text: Raw prompt text with $var placeholders
        kwargs: Optional dictionary of variable substitutions
        **extra_kwargs: Additional variable substitutions

    Returns:
        Formatted prompt text
    """
    substitutions: dict[str, object] = dict(kwargs or {})
    substitutions.update(extra_kwargs)
    template = Template(text)
    return template.safe_substitute(**substitutions)


# MARK: - File Loading


@cache
def load_prompt_text(filename: str, package_name: str) -> str:
    """Load prompt text from package resource.

    Cached on ``(filename, package_name)`` (filename is already the normalized,
    traversal-checked package-relative path). Prompts are effectively static at
    runtime, so caching avoids re-importing the package, re-stat-ing the path,
    and re-scanning the directory on every (possibly per-request) call. The
    tradeoff: live hot-reload of prompt files in dev is disabled until the
    process restarts (accepted per shared-utils-6).

    Attempts loading in order:
    1. Direct file path from package module location
    2. Case-insensitive file match in package directory
    3. Package resources (importlib.resources)

    Args:
        filename: Name of the prompt file
        package_name: Full package name where prompts are located

    Returns:
        Prompt text content

    Raises:
        FileNotFoundError: If prompt file cannot be found
    """
    # Try filesystem-based loading first
    text = _try_load_from_filesystem(filename, package_name)
    if text is not None:
        return text

    # Fall back to package resources
    return _load_from_package_resources(filename, package_name)


def _try_load_from_filesystem(filename: str, package_name: str) -> str | None:
    """Attempt to load prompt from filesystem based on package location.

    Args:
        filename: Name of the prompt file
        package_name: Full package name

    Returns:
        File content if found, None otherwise
    """
    try:
        pkg_module = import_module(package_name)
        pkg_file = getattr(pkg_module, "__file__", None)

        if not isinstance(pkg_file, str):
            return None

        base_dir = Path(pkg_file).parent

        # Try exact match
        prompt_path = base_dir / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")

        # Try case-insensitive match
        matched_path = _find_case_insensitive_file(base_dir, filename)
        if matched_path:
            return matched_path.read_text(encoding="utf-8")

    except (ModuleNotFoundError, ImportError, OSError, AttributeError, ValueError) as exc:
        # Expected-absence fallback: degrade to the importlib.resources path. Log
        # at debug so a real I/O fault (e.g. a corrupt resource) is diagnosable.
        _logger.debug("Filesystem prompt load failed for %r in %r: %s", filename, package_name, exc)
        return None

    return None


def _find_case_insensitive_file(directory: Path, filename: str) -> Path | None:
    """Find file with case-insensitive matching.

    Args:
        directory: Directory to search in
        filename: Target filename (case-insensitive)

    Returns:
        Path to matching file, or None if not found
    """
    filename_lower = filename.lower()
    try:
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.name.lower() == filename_lower:
                return file_path
    except OSError as exc:
        _logger.debug("Case-insensitive scan of %r failed: %s", directory, exc)
        return None
    return None


def _load_from_package_resources(filename: str, package_name: str) -> str:
    """Load prompt from package resources with fallback to case-insensitive lookup.

    Args:
        filename: Name of the prompt file
        package_name: Full package name

    Returns:
        File content

    Raises:
        FileNotFoundError: If file not found in package resources
    """
    # Try exact match
    try:
        return read_resource_text(package_name, filename, encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, ImportError, OSError, ValueError) as exc:
        _logger.debug("Exact resource load failed for %r in %r: %s", filename, package_name, exc)

    # Try case-insensitive lookup
    filename_lower = filename.lower()
    try:
        pkg_files = _resources.files(package_name)
        for resource in pkg_files.iterdir():
            if resource.name.lower() == filename_lower:
                with _resources.as_file(resource) as resource_path:
                    return resource_path.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, ImportError, OSError) as exc:
        _logger.debug(
            "Case-insensitive resource scan failed for %r in %r: %s", filename, package_name, exc
        )

    raise FileNotFoundError(f"Prompt file not found: {filename} in package {package_name}")


# MARK: - Text Processing


def _normalize_prompt_filename(filename: str) -> str:
    """Normalize and validate a package-relative prompt path.

    Allows one or more safe path segments under the prompts package (for example
    ``assignment_agent/job/SCOPE``) but rejects traversal, absolute paths, and
    drive-letter prefixes.

    Args:
        filename: Original filename

    Returns:
        Normalized path ending in ``.md``

    Raises:
        ValueError: If filename is not a safe package-relative Markdown path.
    """
    if not filename:
        raise ValueError("Prompt filename must be a plain Markdown file name")

    if filename != filename.strip():
        raise ValueError("Prompt filename must be a plain Markdown file name")

    normalized = filename.replace("\\", "/")
    if normalized.startswith("/") or ".." in normalized.split("/") or ":" in normalized:
        raise ValueError("Prompt filename must be a plain Markdown file name")

    segments = normalized.split("/")
    if not segments or any(not segment for segment in segments):
        raise ValueError("Prompt filename must be a plain Markdown file name")

    if not segments[-1].lower().endswith(".md"):
        segments[-1] = f"{segments[-1]}.md"

    for segment in segments:
        if not _PROMPT_SEGMENT_RE.fullmatch(segment):
            raise ValueError("Prompt filename must be a plain Markdown file name")

    return "/".join(segments)
