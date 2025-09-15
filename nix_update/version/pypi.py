from __future__ import annotations

from typing import TYPE_CHECKING

from nix_update.utils import info

from .http import fetch_json
from .version import Version

if TYPE_CHECKING:
    from urllib.parse import ParseResult


def fetch_pypi_versions(url: ParseResult) -> list[Version]:
    if url.netloc != "pypi":
        return []
    parts = url.path.split("/")
    package = parts[2]
    pypi_url = f"https://pypi.org/pypi/{package}/json"
    info(f"fetch {pypi_url}")
    data = fetch_json(pypi_url)
    version = data["info"]["version"]
    if not isinstance(version, str):
        msg = f"Expected version to be string, got {type(version)}"
        raise TypeError(msg)
    # TODO look at info->releases instead
    return [Version(version)]
