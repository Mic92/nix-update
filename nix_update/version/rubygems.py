from __future__ import annotations

import json
import urllib.request
from typing import TYPE_CHECKING

from nix_update.errors import VersionError
from nix_update.utils import info

from .http import DEFAULT_TIMEOUT
from .version import Version

if TYPE_CHECKING:
    from urllib.parse import ParseResult


def fetch_rubygem_versions(url: ParseResult) -> list[Version]:
    if url.netloc != "rubygems.org":
        return []
    parts = url.path.split("/")
    gem = parts[-1]
    gem_name, _ = gem.rsplit("-", 1)
    versions_url = f"https://rubygems.org/api/v1/versions/{gem_name}.json"
    info(f"fetch {versions_url}")
    with urllib.request.urlopen(versions_url, timeout=DEFAULT_TIMEOUT) as resp:
        json_versions = json.load(resp)
    if len(json_versions) == 0:
        msg = "No versions found"
        raise VersionError(msg)

    versions: list[Version] = []
    for version in json_versions:
        number = version["number"]
        if not isinstance(number, str):
            msg = f"Expected version number to be string, got {type(number)}"
            raise TypeError(msg)
        prerelease = version["prerelease"]
        if not isinstance(prerelease, bool):
            msg = f"Expected prerelease to be bool, got {type(prerelease)}"
            raise TypeError(msg)
        versions.append(Version(number, prerelease=prerelease))
    return versions
