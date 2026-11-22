"""HTTP utilities for version fetching."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING
from urllib.error import HTTPError
from urllib.request import Request, urlopen

if TYPE_CHECKING:
    from email.message import Message
    from typing import Any

# Default timeout for HTTP requests in seconds
DEFAULT_TIMEOUT = 60

MAX_RETRIES = 4
# Longer waits are not worth blocking an update run for
MAX_RETRY_DELAY = 120
RETRY_STATUS = {429, 503}


def _retry_delay(headers: Message, attempt: int) -> float:
    """Seconds the server asks us to wait, or an exponential backoff."""
    now = time.time()
    retry_after = headers.get("Retry-After", "")
    if retry_after.isdigit():
        return int(retry_after)
    for name in ("RateLimit-Reset", "X-RateLimit-Reset"):
        reset = headers.get(name, "")
        if reset.isdigit():
            # seconds from now, or a Unix timestamp (GitHub, GitLab)
            return int(reset) if int(reset) < now else int(reset) - now
    return 2**attempt


def fetch_json(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
) -> Any:  # noqa: ANN401
    """Fetch JSON from a URL, waiting and retrying when rate limited."""
    request = Request(url, headers=headers or {})
    for attempt in range(MAX_RETRIES + 1):
        try:
            with urlopen(request, timeout=timeout) as resp:
                return json.load(resp)
        except HTTPError as e:
            if e.code not in RETRY_STATUS or attempt == MAX_RETRIES:
                raise
            delay = _retry_delay(e.headers, attempt)
            if delay > MAX_RETRY_DELAY:
                raise
            time.sleep(delay)
    raise AssertionError  # unreachable
