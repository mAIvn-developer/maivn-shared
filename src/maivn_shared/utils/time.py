# pyright: strict
"""Time helpers for UTC timestamps."""

from __future__ import annotations

from datetime import UTC, datetime

# MARK: Time Helpers


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def coerce_utc(value: datetime) -> datetime:
    """Ensure a datetime is timezone-aware, defaulting to UTC for naive values."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def parse_utc_iso(value: str) -> datetime:
    """Parse an ISO datetime string, assuming UTC when tzinfo is missing."""
    return coerce_utc(datetime.fromisoformat(value))
