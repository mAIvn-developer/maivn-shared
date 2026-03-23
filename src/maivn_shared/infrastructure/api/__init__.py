"""API infrastructure for maivn-core.

This module contains API-related infrastructure components
for communication between maivn SDK and maivn-server.
"""

from __future__ import annotations

# MARK: - Endpoints
from .endpoints import ServerEndpoints

__all__ = [
    "ServerEndpoints",
]
