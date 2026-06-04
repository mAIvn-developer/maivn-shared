# pyright: strict
"""Infrastructure layer for maivn-core.

This layer contains infrastructure concerns that support the domain and core layers.

Currently includes:
- MaivnLogger: Cross-package logger for debugging agent flows
- HTTP Client: Shared HTTP communication protocols and implementation
- API Endpoints: Standard endpoint definitions for SDK-server communication
"""

from __future__ import annotations

from .api.endpoints import ServerEndpoints
from .client import (
    HttpClientProtocol,
    SessionClientProtocol,
    SSEClientProtocol,
)
from .http_client import (
    HttpClient,
    HttpError,
)
from .logging import (
    MaivnLogger,
    get_logger,
    get_optional_logger,
)

# MARK: - Exports

__all__ = [
    # HTTP Client
    "HttpClient",
    "HttpError",
    # Client Protocols
    "HttpClientProtocol",
    "SessionClientProtocol",
    "SSEClientProtocol",
    # API
    "ServerEndpoints",
    # Logging
    "MaivnLogger",
    "get_logger",
    "get_optional_logger",
]
