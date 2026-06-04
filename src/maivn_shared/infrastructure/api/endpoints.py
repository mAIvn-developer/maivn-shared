# pyright: strict
"""API endpoint constants for maivn SDK and maivn-server communication.

This module defines the standard API endpoints used for communication
between the maivn SDK and maivn-server.
"""

from __future__ import annotations

from typing import ClassVar

# MARK: - Server Endpoints


class ServerEndpoints:
    """Standard API endpoints for maivn-server."""

    # MARK: - Health
    HEALTH: ClassVar[str] = "/health"

    # MARK: - Session Management
    START_SESSION: ClassVar[str] = "/start-session"
    PREVIEW_REDACTION: ClassVar[str] = "/preview-redaction"
    SESSION_EVENTS: ClassVar[str] = "/sessions/{session_id}/events"
    SESSION_RESUME: ClassVar[str] = "/sessions/{session_id}/resume"


# MARK: - Exports

__all__ = [
    "ServerEndpoints",
]
