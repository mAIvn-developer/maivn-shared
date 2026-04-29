"""PII whitelist configuration for compliance-aware redaction control.

Lets callers explicitly mark certain PII categories or specific values as safe to
leave in cleartext during the redaction pipeline (L1 ingest, L2 tool-result scan,
and L3 shield). The whitelist is **additive** — it only suppresses redaction; it
never causes new PII to flow that wasn't already in the payload.

Compliance posture:
    - Every applied whitelist entry is audited (caller, scope, justification).
    - HIPAA mode (``phi_mode=True``) refuses to whitelist Safe Harbor identifier
      categories; the only safe knobs in that mode are entity-type categories
      that are not Safe Harbor (e.g. URL, generic location > state).
    - SOC-2 / ISO 27001 require documented business justification — every entry
      MUST include a non-empty ``justification`` string.
    - FedRAMP requires that whitelist policy live alongside an admin-controlled
      change record. Whitelist payloads are immutable (frozen Pydantic models)
      so mutation is impossible after construction; replacement is the only
      change mechanism.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# MARK: - HIPAA Safe Harbor Categories

# Categories that may NEVER be whitelisted when ``phi_mode=True``. Mirrors the 18
# HIPAA Safe Harbor identifiers (45 CFR 164.514(b)(2)) mapped to the entity
# types this system can recognize. This list is conservative: any direct
# identifier remains protected even when whitelisted at the entity-type level.
HIPAA_SAFE_HARBOR_CATEGORIES: frozenset[str] = frozenset(
    {
        "person",
        "ssn",
        "phone",
        "fax",
        "email",
        "credit_card",
        "iban",
        "swift",
        "account_id",
        "medical_record_number",
        "health_plan_id",
        "certificate_id",
        "license_id",
        "vehicle_id",
        "device_id",
        "biometric_id",
        "ip_address",
        "url",
        "date",
        "datetime",
    }
)


# MARK: - Whitelist Entry


class PIIWhitelistEntry(BaseModel):
    """A single whitelist rule. Exactly one of entity_type / pattern / value is set.

    Examples::

        # Allow public corporate URLs to flow without redaction.
        PIIWhitelistEntry(
            entity_type="url",
            justification="Marketing site URLs are public; needed for citations.",
        )

        # Allow a single known-safe value.
        PIIWhitelistEntry(
            value="support@maivn.io",
            justification="Public support address listed on documentation.",
        )

        # Allow values matching a regex (use sparingly; broad patterns are risky).
        PIIWhitelistEntry(
            pattern=r"https?://docs\\.maivn\\.io/.*",
            justification="Public docs URLs; whitelisted by request of legal.",
        )
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_type: str | None = Field(
        default=None,
        description=(
            "PII entity type to allow (e.g. 'url', 'ip_address', 'location'). "
            "Mutually exclusive with pattern and value."
        ),
    )
    pattern: str | None = Field(
        default=None,
        description=(
            "Regex matched against detected PII spans (case-insensitive, anchored). "
            "Spans wholly matching the pattern are not redacted. Mutually "
            "exclusive with entity_type and value."
        ),
    )
    value: str | None = Field(
        default=None,
        description=(
            "Literal value to allow. Case-insensitive exact match against the "
            "detected span. Mutually exclusive with entity_type and pattern."
        ),
    )
    justification: str = Field(
        ...,
        min_length=8,
        max_length=512,
        description=(
            "Human-readable business justification. Required for SOC-2 / "
            "ISO 27001 audit evidence. Must be at least 8 characters."
        ),
    )
    label: str | None = Field(
        default=None,
        max_length=128,
        description="Optional human-readable label shown in audit records.",
    )

    @model_validator(mode="after")
    def _exactly_one_kind(self) -> PIIWhitelistEntry:
        provided = sum(
            1 for value in (self.entity_type, self.pattern, self.value) if value is not None
        )
        if provided != 1:
            raise ValueError(
                "PIIWhitelistEntry requires exactly one of entity_type, pattern, or value."
            )
        return self

    @field_validator("entity_type")
    @classmethod
    def _normalize_entity_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("entity_type cannot be blank.")
        return normalized

    @field_validator("pattern")
    @classmethod
    def _validate_pattern(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("pattern cannot be blank.")
        try:
            compiled = re.compile(value, re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {exc}") from exc
        # Refuse trivially permissive patterns that could whitelist huge swaths.
        if compiled.match("") is not None and compiled.match("a") is not None:
            raise ValueError(
                "pattern is too permissive (matches empty or single-char strings); "
                "narrow the pattern or use entity_type."
            )
        return value

    @field_validator("value")
    @classmethod
    def _validate_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        candidate = value.strip()
        if len(candidate) < 3:
            raise ValueError("value must be at least 3 characters after stripping.")
        return candidate

    @field_validator("justification")
    @classmethod
    def _validate_justification(cls, value: str) -> str:
        candidate = value.strip()
        if len(candidate) < 8:
            raise ValueError("justification must be at least 8 characters.")
        return candidate


# MARK: - Whitelist Container


class PIIWhitelist(BaseModel):
    """Collection of PII whitelist entries plus compliance flags.

    Pass to ``Agent`` / ``RedactedMessage`` to suppress redaction of approved
    spans. The whitelist is evaluated **after** PII detection but **before**
    redaction, so detection still occurs (audit trail intact), and only the
    specific approved spans are left in cleartext.

    Compliance flags:
        phi_mode: when True, refuses to construct a whitelist that allows any
            HIPAA Safe Harbor entity-type category. Use for any deployment
            that may handle Protected Health Information.

    Example::

        whitelist = PIIWhitelist(
            entries=[
                PIIWhitelistEntry(
                    entity_type="url",
                    justification="Public docs URLs are needed for citations.",
                ),
            ],
            phi_mode=False,
        )
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    entries: tuple[PIIWhitelistEntry, ...] = Field(
        default_factory=tuple,
        description="Ordered tuple of whitelist entries; immutable after construction.",
    )
    phi_mode: bool = Field(
        default=False,
        description=(
            "When True, refuses HIPAA Safe Harbor entity-type whitelist entries. "
            "Set to True for any deployment that handles PHI."
        ),
    )

    @field_validator("entries", mode="before")
    @classmethod
    def _coerce_entries(cls, value: Any) -> tuple[PIIWhitelistEntry, ...]:
        if value is None:
            return ()
        if isinstance(value, PIIWhitelistEntry):
            return (value,)
        if isinstance(value, list | tuple):
            coerced: list[PIIWhitelistEntry] = []
            for item in value:
                if isinstance(item, PIIWhitelistEntry):
                    coerced.append(item)
                elif isinstance(item, dict):
                    coerced.append(PIIWhitelistEntry.model_validate(item))
                else:
                    raise TypeError(
                        "PIIWhitelist.entries must contain PIIWhitelistEntry or dict items."
                    )
            return tuple(coerced)
        raise TypeError("PIIWhitelist.entries must be a list/tuple/PIIWhitelistEntry.")

    @model_validator(mode="after")
    def _enforce_phi_mode(self) -> PIIWhitelist:
        if not self.phi_mode:
            return self
        bad: list[str] = []
        for entry in self.entries:
            if entry.entity_type and entry.entity_type in HIPAA_SAFE_HARBOR_CATEGORIES:
                bad.append(entry.entity_type)
        if bad:
            raise ValueError(
                "phi_mode=True forbids entity_type whitelist entries for HIPAA Safe "
                f"Harbor categories: {sorted(set(bad))}. Use specific value or "
                "narrowly-scoped pattern entries instead."
            )
        return self

    def is_empty(self) -> bool:
        """Return True if no entries are configured."""
        return len(self.entries) == 0


# MARK: - Public API

__all__ = [
    "HIPAA_SAFE_HARBOR_CATEGORIES",
    "PIIWhitelist",
    "PIIWhitelistEntry",
]
