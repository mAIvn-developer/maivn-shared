"""Utilities for loading and formatting prompts from markdown files."""

from __future__ import annotations

from importlib import resources as _resources
from importlib.resources import read_text as read_resource_text
from pathlib import Path
from string import Template
from typing import Any

# MARK: - Public API


def load_prompt(filename: str, package_name: str, **kwargs: Any) -> str:
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
    normalized_filename = _ensure_md_extension(filename)
    text = _load_prompt_text(normalized_filename, package_name)
    return render_prompt(text, **kwargs)


def render_prompt(text: str, kwargs: dict[str, Any] | None = None, **extra_kwargs: Any) -> str:
    """Format prompt text using Template for safe substitution.

    Args:
        text: Raw prompt text with $var placeholders
        kwargs: Optional dictionary of variable substitutions
        **extra_kwargs: Additional variable substitutions

    Returns:
        Formatted prompt text
    """
    substitutions = dict(kwargs or {})
    substitutions.update(extra_kwargs)
    template = Template(text)
    return template.safe_substitute(**substitutions)


# MARK: - File Loading


def _load_prompt_text(filename: str, package_name: str) -> str:
    """Load prompt text from package resource.

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
        pkg_module = __import__(package_name, fromlist=[""])
        pkg_file = getattr(pkg_module, "__file__", None)

        if not pkg_file:
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

    except (ModuleNotFoundError, ImportError, OSError, AttributeError, ValueError):
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
    except OSError:
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
    if "/" in filename or "\\" in filename:
        normalized = filename.replace("\\", "/")
        parts = [part for part in normalized.split("/") if part]
        try:
            resource = _resources.files(package_name)
            for part in parts:
                resource = _join_resource_case_insensitive(resource, part)
            if resource.is_file():
                with _resources.as_file(resource) as resource_path:
                    return resource_path.read_text(encoding="utf-8")
        except (FileNotFoundError, ModuleNotFoundError, ImportError, OSError, ValueError):
            pass

        raise FileNotFoundError(f"Prompt file not found: {filename} in package {package_name}")

    # Try exact match
    try:
        return read_resource_text(package_name, filename, encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, ImportError, OSError, ValueError):
        pass

    # Try case-insensitive lookup
    filename_lower = filename.lower()
    try:
        pkg_files = _resources.files(package_name)
        for resource in pkg_files.iterdir():
            if resource.name.lower() == filename_lower:
                with _resources.as_file(resource) as resource_path:
                    return resource_path.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, ImportError, OSError):
        pass

    raise FileNotFoundError(f"Prompt file not found: {filename} in package {package_name}")


def _join_resource_case_insensitive(resource: Any, target_name: str) -> Any:
    target_lower = target_name.lower()
    try:
        for child in resource.iterdir():
            if child.name.lower() == target_lower:
                return child
    except (AttributeError, FileNotFoundError, OSError, ValueError):
        return resource.joinpath(target_name)
    return resource.joinpath(target_name)


# MARK: - Text Processing


def _ensure_md_extension(filename: str) -> str:
    """Ensure filename has .md extension.

    Args:
        filename: Original filename

    Returns:
        Filename with .md extension
    """
    return filename if filename.endswith(".md") else f"{filename}.md"
