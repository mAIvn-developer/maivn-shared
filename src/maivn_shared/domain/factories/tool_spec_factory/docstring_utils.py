from __future__ import annotations

from collections.abc import Callable

# MARK: - Constants

_SECTION_MARKERS = ("args:", "returns:", "raises:", "note:", "example:")
_ARGS_END_MARKERS = ("returns:", "raises:", "note:", "example:")

# MARK: - Public Functions


def _extract_function_description(func: Callable[..., object]) -> str:
    """Extract the main description from a function's docstring.

    Takes the first paragraph before 'Args:' section.
    """
    docstring = func.__doc__ or ""
    if not docstring:
        return _default_description(func.__name__)

    description = _extract_description_text(docstring)
    return description or _default_description(func.__name__)


def _parse_docstring_args(docstring: str) -> dict[str, str]:
    """Parse the Args section from a docstring."""
    if not docstring:
        return {}

    lines = docstring.split("\n")
    return _parse_args_section(lines)


# MARK: - Private Helpers


def _default_description(func_name: str) -> str:
    """Generate default description for a function."""
    return f"Execute the {func_name} function."


def _extract_description_text(docstring: str) -> str:
    """Extract description text from docstring, stopping at section markers."""
    lines = docstring.strip().split("\n")
    description_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if _is_section_marker(stripped):
            break
        description_lines.append(stripped)

    description = " ".join(description_lines).strip()
    return " ".join(description.split())


def _is_section_marker(line: str) -> bool:
    """Check if a line is a docstring section marker."""
    return line.lower().startswith(_SECTION_MARKERS)


def _parse_args_section(lines: list[str]) -> dict[str, str]:
    """Parse the Args section from docstring lines."""
    param_docs: dict[str, str] = {}
    in_args_section = False
    current_param: str | None = None
    current_desc: list[str] = []

    for line in lines:
        stripped = line.strip()

        if stripped.lower() == "args:":
            in_args_section = True
            continue

        if not in_args_section:
            continue

        if _is_args_section_end(stripped):
            _save_param(param_docs, current_param, current_desc)
            break

        current_param, current_desc = _process_args_line(
            stripped, param_docs, current_param, current_desc
        )

    _save_param(param_docs, current_param, current_desc)
    return param_docs


def _is_args_section_end(line: str) -> bool:
    """Check if a line marks the end of the Args section."""
    return line.lower().startswith(_ARGS_END_MARKERS)


def _process_args_line(
    stripped: str,
    param_docs: dict[str, str],
    current_param: str | None,
    current_desc: list[str],
) -> tuple[str | None, list[str]]:
    """Process a single line within the Args section."""
    if ":" in stripped and not stripped.startswith(" "):
        _save_param(param_docs, current_param, current_desc)
        return _parse_param_line(stripped)

    if current_param and stripped:
        current_desc.append(stripped)

    return current_param, current_desc


def _parse_param_line(line: str) -> tuple[str, list[str]]:
    """Parse a parameter definition line."""
    parts = line.split(":", 1)
    param_name = parts[0].strip()
    desc = [parts[1].strip()] if len(parts) > 1 and parts[1].strip() else []
    return param_name, desc


def _save_param(
    param_docs: dict[str, str],
    param: str | None,
    desc: list[str],
) -> None:
    """Save a parameter and its description to the docs dict."""
    if param and desc and param not in param_docs:
        param_docs[param] = " ".join(desc).strip()
