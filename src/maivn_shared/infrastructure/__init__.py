"""Infrastructure layer for maivn-core.

This layer contains infrastructure concerns that support the domain and core layers.

Currently includes:
- MaivnLogger: Cross-package logger for debugging agent flows
- HTTP Client: Shared HTTP communication protocols and implementation
- API Endpoints: Standard endpoint definitions for SDK-server communication
"""

from __future__ import annotations

# MARK: API
from .api.endpoints import ServerEndpoints

# MARK: Client Protocols
from .client import (
    HttpClientProtocol,
    SessionClientProtocol,
    SSEClientProtocol,
)

# MARK: HTTP
from .http_client import (
    HttpClient,
    HttpError,
)

# MARK: Logging
from .logging import (
    MaivnLogger,
    get_logger,
    get_optional_logger,
)

__all__ = [
    # MARK: - HTTP Client
    "HttpClient",
    "HttpError",
    # MARK: - Client Protocols
    "HttpClientProtocol",
    "SessionClientProtocol",
    "SSEClientProtocol",
    # MARK: - API
    "ServerEndpoints",
    # MARK: - Logging
    "MaivnLogger",
    "get_logger",
    "get_optional_logger",
]
