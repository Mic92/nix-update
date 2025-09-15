"""HTTP utilities for version fetching."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from urllib.request import urlopen

if TYPE_CHECKING:
    from typing import Any

# Default timeout for HTTP requests in seconds
DEFAULT_TIMEOUT = 60


def fetch_json(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Any:  # noqa: ANN401
    """Fetch JSON data from a URL with proper timeout and error handling."""
    with urlopen(url, timeout=timeout) as resp:
        return json.load(resp)
