from __future__ import annotations

from typing import TYPE_CHECKING

from nix_update.utils import info

from .http import fetch_json
from .version import Version

if TYPE_CHECKING:
    from urllib.parse import ParseResult


def fetch_npm_versions(url: ParseResult) -> list[Version]:
    if url.netloc != "registry.npmjs.org":
        return []
    parts = url.path.split("/")
    # Handle scoped packages like @myorg/mypackage
    package = f"{parts[1]}/{parts[2]}" if parts[1].startswith("@") else parts[1]
    npm_url = f"https://registry.npmjs.org/{package}/latest"
    info(f"fetch {npm_url}")
    data = fetch_json(npm_url)
    return [Version(data["version"])]
