from __future__ import annotations

import io
from email.message import Message
from typing import TYPE_CHECKING
from urllib.error import HTTPError

import pytest

from nix_update.version import http

if TYPE_CHECKING:
    from urllib.request import Request


class FakeServer:
    """Answers with the given statuses in turn, then with ``{}``."""

    def __init__(
        self, monkeypatch: pytest.MonkeyPatch, *responses: dict[str, str]
    ) -> None:
        self.responses = list(responses)
        self.slept: list[float] = []
        monkeypatch.setattr(http, "urlopen", self.urlopen)
        monkeypatch.setattr(http.time, "sleep", self.slept.append)

    def urlopen(self, request: Request, timeout: float | None = None) -> io.BytesIO:
        del timeout
        if not self.responses:
            return io.BytesIO(b"{}")
        headers = Message()
        for key, value in self.responses.pop(0).items():
            headers[key] = value
        code = int(headers.get("status", "429"))
        raise HTTPError(request.full_url, code, "error", headers, None)


def test_retry_after_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    server = FakeServer(monkeypatch, {"Retry-After": "7"})
    assert http.fetch_json("https://example.com") == {}
    assert server.slept == [7]


def test_backs_off_then_gives_up(monkeypatch: pytest.MonkeyPatch) -> None:
    server = FakeServer(monkeypatch, {"status": "503"}, *[{}] * 10)
    with pytest.raises(HTTPError):
        http.fetch_json("https://example.com")
    assert server.slept == [1, 2, 4, 8]


def test_does_not_wait_for_long_delays(monkeypatch: pytest.MonkeyPatch) -> None:
    server = FakeServer(monkeypatch, {"Retry-After": "3600"})
    with pytest.raises(HTTPError):
        http.fetch_json("https://example.com")
    assert server.slept == []
