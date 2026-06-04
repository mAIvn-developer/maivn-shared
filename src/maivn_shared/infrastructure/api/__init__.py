# pyright: strict
"""API infrastructure for maivn-core.

This module contains API-related infrastructure components
for communication between maivn SDK and maivn-server.
"""

from __future__ import annotations

from .endpoints import ServerEndpoints

# MARK: - Exports

__all__ = [
    "ServerEndpoints",
]
