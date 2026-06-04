"""Provider metadata models for toolsets.

``ProviderMetadata`` describes a toolset's identity, supported auth modes, the
scopes it can request, and the capabilities it advertises. The metadata is
serializable so it can be inspected by hosts, recorded in audit logs, or
surfaced in user-facing catalogs.

Metadata must never contain secrets. Tokens, client secrets, and credential
material are stored elsewhere (typically in a connector-runtime layer) and only
referenced from metadata via redacted handles.
"""

# pyright: strict
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from pydantic import JsonValue

# MARK: Authentication


class AuthMode(str, Enum):
    """Supported authentication flows for a toolset / provider."""

    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2_AUTH_CODE = "oauth2_auth_code"
    OAUTH2_PKCE = "oauth2_pkce"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"
    OAUTH2_DEVICE_CODE = "oauth2_device_code"
    SERVICE_ACCOUNT = "service_account"
    CUSTOM = "custom"


# MARK: Capabilities


class ProviderCapability(str, Enum):
    """Standard capability flags a toolset may advertise."""

    READ = "read"
    WRITE = "write"
    SEARCH = "search"
    EXPORT = "export"
    IMPORT = "import"
    WEBHOOKS = "webhooks"
    STREAMING = "streaming"
    BULK = "bulk"
    DRY_RUN = "dry_run"
    PAGINATION = "pagination"
    RATE_LIMITED = "rate_limited"


# MARK: Metadata


def _empty_scopes() -> dict[str, str]:
    return {}


def _empty_capabilities() -> frozenset[ProviderCapability]:
    return frozenset()


def _empty_extras() -> dict[str, JsonValue]:
    return {}


@dataclass(frozen=True)
class ProviderMetadata:
    """Static metadata describing a toolset / provider.

    Attributes:
        name: Stable machine-friendly provider name (``"gmail"``, ``"github"``).
        display_name: Human-readable name for catalogs and docs.
        version: Toolset implementation version, independent of the provider
            API version.
        description: One-paragraph public description suitable for catalogs.
        auth_modes: Auth flows this toolset supports.
        scopes: Catalog of scopes/permissions this toolset understands. The
            value for each key is a short public description.
        capabilities: Standard capability flags this toolset advertises.
        documentation_url: Public URL pointing to provider documentation.
        homepage_url: Provider homepage.
        tags: Free-form tags used for grouping in toolset catalogs.
        extras: Toolset-specific metadata. Must be JSON-serializable and must
            not contain secrets.
    """

    name: str
    display_name: str
    version: str
    description: str = ""
    auth_modes: tuple[AuthMode, ...] = ()
    scopes: dict[str, str] = field(default_factory=_empty_scopes)
    capabilities: frozenset[ProviderCapability] = field(default_factory=_empty_capabilities)
    documentation_url: str | None = None
    homepage_url: str | None = None
    tags: tuple[str, ...] = ()
    extras: dict[str, JsonValue] = field(default_factory=_empty_extras)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ProviderMetadata.name is required")
        if not self.display_name:
            raise ValueError("ProviderMetadata.display_name is required")
        if not self.version:
            raise ValueError("ProviderMetadata.version is required")

    def supports_auth(self, mode: AuthMode) -> bool:
        """Return True when this provider supports ``mode``."""
        return mode in self.auth_modes

    def has_capability(self, capability: ProviderCapability) -> bool:
        """Return True when this provider advertises ``capability``."""
        return capability in self.capabilities

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a JSON-serializable representation of this metadata."""
        auth_modes: list[JsonValue] = [mode.value for mode in self.auth_modes]
        scopes: dict[str, JsonValue] = dict(self.scopes)
        capabilities: list[JsonValue] = [
            value for value in sorted(c.value for c in self.capabilities)
        ]
        tags: list[JsonValue] = list(self.tags)
        extras: dict[str, JsonValue] = dict(self.extras)
        return {
            "name": self.name,
            "display_name": self.display_name,
            "version": self.version,
            "description": self.description,
            "auth_modes": auth_modes,
            "scopes": scopes,
            "capabilities": capabilities,
            "documentation_url": self.documentation_url,
            "homepage_url": self.homepage_url,
            "tags": tags,
            "extras": extras,
        }
