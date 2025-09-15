from __future__ import annotations

from typing import TYPE_CHECKING

from nix_update.utils import info

from .http import fetch_json
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
    data = fetch_json(crate_url)
    return [
        Version(version["num"]) for version in data["versions"] if not version["yanked"]
    ]
