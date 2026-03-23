"""Protocol definitions for HTTP client communication.

This module defines interfaces for HTTP clients and session clients,
enabling flexible implementation and testing for maivn SDK and maivn-server communication.
"""

from __future__ import annotations

from typing import Any, Protocol

# MARK: - HTTP Client Protocol


class HttpClientProtocol(Protocol):
    """Protocol for HTTP client implementations."""

    def post(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Perform HTTP POST request.

        Args:
            url: Target URL
            json: JSON payload
            headers: HTTP headers
            timeout: Request timeout in seconds

        Returns:
            Response JSON data

        Raises:
            HttpError: If request fails
        """
        ...

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Perform HTTP GET request.

        Args:
            url: Target URL
            headers: HTTP headers
            timeout: Request timeout in seconds

        Returns:
            Response JSON data

        Raises:
            HttpError: If request fails
        """
        ...


# MARK: - Session Client Protocol


class SessionClientProtocol(Protocol):
    """Protocol for session client implementations."""

    @property
    def api_key(self) -> str | None:
        """Get the API key for authentication."""
        ...

    @property
    def base_url(self) -> str | None:
        """Get the base URL for API requests."""
        ...

    @property
    def timeout(self) -> float | None:
        """Get the default timeout for requests."""
        ...

    def headers(self) -> dict[str, str]:
        """Get headers for authenticated requests.

        Returns:
            Dictionary of HTTP headers

        Raises:
            ValueError: If API key is not configured
        """
        ...

    def start_session(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        """Start a session via the server.

        Args:
            payload: Session configuration payload, typically encoded from a
                SessionStartRequest instance.

        Returns:
            Server response with session details

        Raises:
            HttpError: If session start fails
        """
        ...

    def get_thread_id(self, create_if_missing: bool = False) -> str | None:
        """Get the current thread ID.

        Args:
            create_if_missing: Whether to create a new thread ID if none exists

        Returns:
            Thread ID or None if not set and not creating
        """
        ...

    def set_thread_id(self, thread_id: str) -> None:
        """Set the thread ID.

        Args:
            thread_id: Thread identifier to set

        Raises:
            ValueError: If thread_id is invalid
        """
        ...


# MARK: - SSE Client Protocol


class SSEClientProtocol(Protocol):
    """Protocol for Server-Sent Events client implementations."""

    def iter_events(self, url: str) -> Any:
        """Iterate over server-sent events.

        Args:
            url: URL of the SSE endpoint

        Returns:
            Iterator of SSE events

        Raises:
            ConnectionError: If unable to connect to SSE endpoint
        """
        ...


# MARK: - Exports

__all__ = [
    "HttpClientProtocol",
    "SessionClientProtocol",
    "SSEClientProtocol",
]
