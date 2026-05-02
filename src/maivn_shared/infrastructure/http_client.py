"""HTTP client implementation using httpx.

This module provides a concrete implementation of the HttpClientProtocol
using the httpx library for making HTTP requests.
"""

from __future__ import annotations

import threading
import weakref
from typing import Any

import httpx

from .client import HttpClientProtocol

_DEFAULT_TIMEOUT_SECONDS: float = 600.0
_MAX_REQUEST_ERROR_MESSAGE_CHARS: int = 200

# MARK: - Exceptions


class HttpError(Exception):
    """Exception raised for HTTP request errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


# MARK: - HTTP Client


class HttpClient(HttpClientProtocol):
    """HTTP client implementation using httpx."""

    def __init__(self, *, timeout: float | None = None) -> None:
        """Initialize the HTTP client.

        Args:
            timeout: Default timeout for requests
        """
        self._timeout = timeout if timeout is not None else _DEFAULT_TIMEOUT_SECONDS
        self._clients_lock = threading.RLock()
        self._thread_local = threading.local()
        self._clients: weakref.WeakSet[httpx.Client] = weakref.WeakSet()

    # MARK: - Public Methods

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
        return self._execute_request("POST", url, json=json, headers=headers, timeout=timeout)

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
        return self._execute_request("GET", url, headers=headers, timeout=timeout)

    # MARK: - Private Methods

    def _execute_request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Execute an HTTP request with unified error handling."""
        request_timeout = timeout if timeout is not None else self._timeout

        try:
            client = self._get_client()
            response = client.request(
                method,
                url,
                json=json,
                headers=headers,
                timeout=request_timeout,
            )
            response.raise_for_status()
            return self._parse_response(response)
        except httpx.HTTPStatusError as e:
            raise self._create_http_status_error(e) from e
        except httpx.RequestError as e:
            raise HttpError(self._create_request_error_message(e)) from e
        except Exception as e:
            raise HttpError(f"Unexpected error: {e}") from e

    def _create_client(self, timeout: float) -> httpx.Client:
        """Create an httpx client with connection pooling."""
        return httpx.Client(
            timeout=timeout,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            headers={
                "Connection": "keep-alive",
                "Keep-Alive": "timeout=300",
            },
        )

    def _get_client(self) -> httpx.Client:
        client = getattr(self._thread_local, "client", None)
        if client is None or getattr(client, "is_closed", False):
            client = self._create_client(self._timeout)
            self._thread_local.client = client
            with self._clients_lock:
                self._clients.add(client)
        return client

    def close(self) -> None:
        """Close underlying HTTP connections."""
        with self._clients_lock:
            clients = list(self._clients)
            self._clients.clear()

        for client in clients:
            if not getattr(client, "is_closed", False):
                client.close()

        if hasattr(self._thread_local, "client"):
            del self._thread_local.client

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        del exc_type, exc_val, exc_tb
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def _parse_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse HTTP response to JSON.

        Args:
            response: httpx Response object

        Returns:
            Parsed JSON data or empty dict if no content
        """
        return response.json() if response.content else {}

    def _create_http_status_error(self, error: httpx.HTTPStatusError) -> HttpError:
        """Create HttpError from httpx HTTPStatusError.

        Args:
            error: httpx HTTPStatusError

        Returns:
            HttpError with status code and message
        """
        reason = error.response.reason_phrase.strip()
        reason_text = f" {reason}" if reason else ""
        request_summary = self._request_summary(error.request)
        return HttpError(
            f"HTTP {error.response.status_code}{reason_text}{request_summary}",
            status_code=error.response.status_code,
        )

    def _create_request_error_message(self, error: httpx.RequestError) -> str:
        """Create a request-error message without leaking URL query parameters."""
        raw_message = str(error.args[0]) if error.args else type(error).__name__
        message = self._truncate_error_message(raw_message)
        return f"Request failed: {message}{self._request_summary(error.request)}"

    @staticmethod
    def _request_summary(request: httpx.Request | None) -> str:
        """Return a compact request summary with the query string stripped."""
        if request is None:
            return ""
        safe_url = request.url.copy_with(query=None)
        return f" ({request.method} {safe_url})"

    @staticmethod
    def _truncate_error_message(message: str) -> str:
        """Keep request error messages bounded before callers log them."""
        if len(message) <= _MAX_REQUEST_ERROR_MESSAGE_CHARS:
            return message
        return f"{message[: _MAX_REQUEST_ERROR_MESSAGE_CHARS - 3]}..."


# MARK: - Module Exports

__all__ = [
    "HttpClient",
    "HttpError",
]
