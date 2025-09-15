from __future__ import annotations

import json
import urllib.request
from typing import TYPE_CHECKING

from nix_update.utils import info

from .http import DEFAULT_TIMEOUT
from .version import Version

if TYPE_CHECKING:
    from urllib.parse import ParseResult


def fetch_crate_versions(url: ParseResult) -> list[Version]:
    if url.netloc != "crates.io":
        return []
    parts = url.path.split("/")
    package = parts[4]
    crate_url = f"https://crates.io/api/v1/crates/{package}/versions"
    info(f"fetch {crate_url}")
    with urllib.request.urlopen(crate_url, timeout=DEFAULT_TIMEOUT) as resp:
        data = json.load(resp)
    return [
        Version(version["num"]) for version in data["versions"] if not version["yanked"]
    ]
