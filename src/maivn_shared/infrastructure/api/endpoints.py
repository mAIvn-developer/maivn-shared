"""API endpoint constants for maivn SDK and maivn-server communication.

This module defines the standard API endpoints used for communication
between the maivn SDK and maivn-server.
"""

from __future__ import annotations

# MARK: - Server Endpoints


class ServerEndpoints:
    """Standard API endpoints for maivn-server."""

    # MARK: - Health
    HEALTH = "/health"

    # MARK: - Session Management
    START_SESSION = "/start-session"
    PREVIEW_REDACTION = "/preview-redaction"
    SESSION_EVENTS = "/sessions/{session_id}/events"
    SESSION_RESUME = "/sessions/{session_id}/resume"


# MARK: - Exports

__all__ = [
    "ServerEndpoints",
]
