from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from time import sleep

import httpx
import pytest

from maivn_shared.infrastructure.http_client import HttpClient, HttpError


def test_http_client_reuses_single_client_and_honors_request_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[object] = []
    calls: list[dict[str, object]] = []

    class _StubClient:
        def __init__(self, *args, **kwargs) -> None:
            del args
            self.is_closed = False
            created.append(kwargs)

        def request(
            self,
            method: str,
            url: str,
            *,
            json: dict[str, object] | None = None,
            headers: dict[str, str] | None = None,
            timeout: float | None = None,
        ) -> httpx.Response:
            calls.append(
                {
                    "method": method,
                    "url": url,
                    "json": json,
                    "headers": headers,
                    "timeout": timeout,
                }
            )
            return httpx.Response(
                status_code=200,
                json={"ok": True},
                request=httpx.Request(method, url),
            )

        def close(self) -> None:
            self.is_closed = True

    monkeypatch.setattr(httpx, "Client", _StubClient)

    client = HttpClient(timeout=7.5)
    first = client.get("https://example.com/a")
    second = client.post("https://example.com/b", json={"value": 1}, timeout=2.0)

    assert first == {"ok": True}
    assert second == {"ok": True}
    assert len(created) == 1
    assert calls[0]["timeout"] == 7.5
    assert calls[1]["timeout"] == 2.0

    client.close()
    client.get("https://example.com/c")
    assert len(created) == 2


def test_http_client_wraps_request_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class _StubClient:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs
            self.is_closed = False

        def request(self, method: str, url: str, **kwargs) -> httpx.Response:
            del kwargs
            request = httpx.Request(method, url)
            raise httpx.RequestError("network down", request=request)

        def close(self) -> None:
            self.is_closed = True

    monkeypatch.setattr(httpx, "Client", _StubClient)

    client = HttpClient()
    with pytest.raises(HttpError, match="Request failed"):
        client.get("https://example.com/fail")


def test_http_client_uses_separate_clients_per_thread_for_parallel_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[object] = []

    class _StubClient:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs
            self.is_closed = False
            self._in_request = False
            created.append(self)

        def request(self, method: str, url: str, **kwargs) -> httpx.Response:
            del kwargs
            if self._in_request:
                raise RuntimeError("concurrent request on shared client")
            self._in_request = True
            try:
                sleep(0.05)
                return httpx.Response(
                    status_code=200,
                    json={"ok": True, "client_id": id(self)},
                    request=httpx.Request(method, url),
                )
            finally:
                self._in_request = False

        def close(self) -> None:
            self.is_closed = True

    monkeypatch.setattr(httpx, "Client", _StubClient)

    client = HttpClient()
    start = threading.Barrier(3)

    def _do_get() -> dict[str, object]:
        start.wait()
        return client.get("https://example.com/concurrent")

    with ThreadPoolExecutor(max_workers=2) as executor:
        left = executor.submit(_do_get)
        right = executor.submit(_do_get)
        start.wait()
        left_result = left.result()
        right_result = right.result()

    assert left_result["ok"] is True
    assert right_result["ok"] is True
    assert left_result["client_id"] != right_result["client_id"]
    assert len(created) == 2
