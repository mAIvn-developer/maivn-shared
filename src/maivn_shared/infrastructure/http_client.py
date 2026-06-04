# pyright: strict
"""HTTP client implementation using httpx.

This module provides a concrete implementation of the HttpClientProtocol
using the httpx library for making HTTP requests.
"""

from __future__ import annotations

import threading
import weakref
from types import TracebackType
from typing import cast

import httpx
from pydantic import JsonValue
from typing_extensions import override

from .client import HttpClientProtocol, JsonObject

_DEFAULT_TIMEOUT_SECONDS: float = 600.0


# MARK: - Types


class _ClientLocal(threading.local):
    client: httpx.Client | None = None


# MARK: - Exceptions


class HttpError(Exception):
    """Exception raised for HTTP request errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code: int | None = status_code


# MARK: - HTTP Client


class HttpClient(HttpClientProtocol):
    """HTTP client implementation using httpx."""

    def __init__(self, *, timeout: float | None = None) -> None:
        """Initialize the HTTP client.

        Args:
            timeout: Default timeout for requests
        """
        self._timeout: float = timeout if timeout is not None else _DEFAULT_TIMEOUT_SECONDS
        self._clients_lock: threading.RLock = threading.RLock()
        self._thread_local: _ClientLocal = _ClientLocal()
        self._clients: weakref.WeakSet[httpx.Client] = weakref.WeakSet()

    # MARK: - Public Methods

    @override
    def post(
        self,
        url: str,
        *,
        json: JsonObject | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> JsonValue:
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

    @override
    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> JsonValue:
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
        json: JsonObject | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> JsonValue:
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
            _ = response.raise_for_status()
            return self._parse_response(response)
        except httpx.HTTPStatusError as e:
            raise self._create_http_status_error(e) from e
        except httpx.RequestError as e:
            raise HttpError(self._create_request_error_message(e)) from e
        except Exception as e:  # noqa: BLE001 - preserve public HttpError wrapping.
            raise HttpError(f"Unexpected error: {type(e).__name__}") from e

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
        client = self._thread_local.client
        if client is None or client.is_closed:
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
            if not client.is_closed:
                client.close()

        self._thread_local.client = None

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        del exc_type, exc_val, exc_tb
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:  # noqa: BLE001 - finalizers must not raise during GC.
            pass

    def _parse_response(self, response: httpx.Response) -> JsonValue:
        """Parse HTTP response to JSON.

        Args:
            response: httpx Response object

        Returns:
            Parsed JSON data or empty dict if no content
        """
        if not response.content:
            return {}
        parsed = cast(object, response.json())
        return cast(JsonValue, parsed)

    def _create_http_status_error(self, error: httpx.HTTPStatusError) -> HttpError:
        """Create HttpError from httpx HTTPStatusError.

        Args:
            error: httpx HTTPStatusError

        Returns:
            HttpError with status code and message
        """
        return HttpError(
            f"HTTP {error.response.status_code} response failed.",
            status_code=error.response.status_code,
        )

    def _create_request_error_message(self, error: httpx.RequestError) -> str:
        """Create a request-error message without leaking request details."""
        return f"Request failed: {type(error).__name__}"


# MARK: - Module Exports

__all__ = [
    "HttpClient",
    "HttpError",
]
