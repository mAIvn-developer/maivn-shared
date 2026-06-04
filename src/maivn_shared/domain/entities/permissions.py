"""Permission model for toolset method tools.

Each tool exposed through ``@toolify`` may declare the categories of work it
performs. Hosts can inspect those flags to enforce least-privilege defaults,
surface warnings in their UI, or refuse to register destructive tools without
explicit opt-in. The SDK uses the declared flags to auto-derive filter tags
(``"read"``, ``"write"``, ``"destructive"``) at ``add_toolset`` time.

The model is intentionally small. The flags are explicit, the
:class:`PermissionSet` is immutable, and there is no implicit upgrade between
flags. Holding :data:`PermissionFlag.WRITE` does **not** grant
:data:`PermissionFlag.DELETE`.
"""

# pyright: strict
from __future__ import annotations

from collections.abc import Iterable
from enum import Flag, auto
from typing import TYPE_CHECKING, ClassVar, cast

from typing_extensions import override

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema


class PermissionFlag(Flag):
    """Categories of work a tool may perform.

    Flags compose with the bitwise ``|`` operator::

        rw = PermissionFlag.READ | PermissionFlag.WRITE
    """

    NONE = 0
    READ = auto()
    WRITE = auto()
    DELETE = auto()
    EXPORT = auto()
    IMPORT = auto()
    ADMIN = auto()
    IMPERSONATE = auto()


PERMISSION_FLAG_NAMES: dict[PermissionFlag, str] = {
    PermissionFlag.READ: "read",
    PermissionFlag.WRITE: "write",
    PermissionFlag.DELETE: "delete",
    PermissionFlag.EXPORT: "export",
    PermissionFlag.IMPORT: "import",
    PermissionFlag.ADMIN: "admin",
    PermissionFlag.IMPERSONATE: "impersonate",
}

NAME_TO_PERMISSION_FLAG: dict[str, PermissionFlag] = {
    name: flag for flag, name in PERMISSION_FLAG_NAMES.items()
}


DESTRUCTIVE_FLAG_NAMES: frozenset[str] = frozenset({"delete", "import", "admin", "impersonate"})


class PermissionSet:
    """Immutable set of permission flags with helpful inspection helpers."""

    __slots__: ClassVar[tuple[str, ...]] = ("_flags",)

    _flags: PermissionFlag

    def __init__(self, flags: PermissionFlag = PermissionFlag.NONE) -> None:
        self._flags = flags

    @classmethod
    def from_names(cls, names: Iterable[str]) -> PermissionSet:
        """Build a :class:`PermissionSet` from canonical flag names."""
        unknown: list[str] = []
        accumulator = PermissionFlag.NONE
        for name in names:
            flag = NAME_TO_PERMISSION_FLAG.get(name)
            if flag is None:
                unknown.append(name)
                continue
            accumulator |= flag
        if unknown:
            raise ValueError(f"Unknown permission flags: {sorted(unknown)!r}")
        return cls(accumulator)

    @classmethod
    def all(cls) -> PermissionSet:
        """Return a permission set containing every defined flag."""
        flags = PermissionFlag.NONE
        for flag in PERMISSION_FLAG_NAMES:
            flags |= flag
        return cls(flags)

    @property
    def flags(self) -> PermissionFlag:
        """Return the underlying bitfield."""
        return self._flags

    def includes(self, flag: PermissionFlag) -> bool:
        """Return True if every bit in ``flag`` is present."""
        return (self._flags & flag) == flag

    def is_empty(self) -> bool:
        """Return True when no flag is set."""
        return self._flags == PermissionFlag.NONE

    def is_destructive(self) -> bool:
        """Return True when this set includes any destructive flag.

        ``DELETE``, ``IMPORT``, ``ADMIN``, and ``IMPERSONATE`` are treated as
        destructive because they can either remove data, mutate large amounts
        of data, or act on behalf of another principal.
        """
        destructive = (
            PermissionFlag.DELETE
            | PermissionFlag.IMPORT
            | PermissionFlag.ADMIN
            | PermissionFlag.IMPERSONATE
        )
        return bool(self._flags & destructive)

    def to_list(self) -> list[str]:
        """Return the canonical flag names contained in this set, sorted."""
        return sorted(
            PERMISSION_FLAG_NAMES[flag] for flag in PERMISSION_FLAG_NAMES if flag & self._flags
        )

    def __or__(self, other: PermissionSet | PermissionFlag) -> PermissionSet:
        flags = other._flags if isinstance(other, PermissionSet) else other
        return PermissionSet(self._flags | flags)

    def __and__(self, other: PermissionSet | PermissionFlag) -> PermissionSet:
        flags = other._flags if isinstance(other, PermissionSet) else other
        return PermissionSet(self._flags & flags)

    def __contains__(self, flag: object) -> bool:
        if isinstance(flag, PermissionFlag):
            return self.includes(flag)
        return False

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, PermissionSet):
            return self._flags == other._flags
        if isinstance(other, PermissionFlag):
            return self._flags == other
        return NotImplemented

    @override
    def __hash__(self) -> int:
        return hash(self._flags)

    @override
    def __repr__(self) -> str:
        return f"PermissionSet({self.to_list()!r})"

    # MARK: Pydantic integration

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: object,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Teach Pydantic v2 how to validate / serialize a PermissionSet.

        Validation accepts either an existing :class:`PermissionSet`
        (passed through unchanged) or a list of canonical flag names
        (constructed via :meth:`from_names`). Serialization emits the
        sorted flag-name list produced by :meth:`to_list`, which keeps
        the wire shape stable across processes and survives
        ``model_dump(mode="json")``.
        """
        from pydantic_core import core_schema

        return core_schema.no_info_plain_validator_function(
            cls._pydantic_validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._pydantic_serialize,
                return_schema=core_schema.list_schema(core_schema.str_schema()),
                when_used="always",
            ),
        )

    @classmethod
    def _pydantic_validate(cls, value: object) -> PermissionSet:
        """Validator for Pydantic field assignment."""
        if isinstance(value, PermissionSet):
            return value
        if isinstance(value, PermissionFlag):
            return PermissionSet(value)
        if isinstance(value, list | tuple | set | frozenset):
            return cls.from_names(cast(Iterable[str], value))
        message = (
            "PermissionSet expected a PermissionSet, PermissionFlag, or "
            + f"iterable of flag names; got {type(value).__name__}"
        )
        raise TypeError(message)

    @staticmethod
    def _pydantic_serialize(value: PermissionSet) -> list[str]:
        """Serialize a PermissionSet for Pydantic."""
        return value.to_list()


def require_permissions(
    granted: PermissionSet,
    required: PermissionSet | PermissionFlag,
) -> None:
    """Raise :class:`PermissionError` if ``granted`` lacks any required flag.

    Hosts that want to wrap tools with their own authorization layer can call
    this helper to validate the caller's permission grant against the tool's
    declared permission set.
    """
    required_set = required if isinstance(required, PermissionSet) else PermissionSet(required)
    missing_flags = required_set.flags & ~granted.flags
    if missing_flags:
        missing = PermissionSet(missing_flags).to_list()
        raise PermissionError(f"Missing required permissions: {missing!r}")
