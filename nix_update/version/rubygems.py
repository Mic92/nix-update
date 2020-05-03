import urllib.request
from typing import Optional
from urllib.parse import ParseResult
import json

from ..errors import VersionError
from ..utils import info


def fetch_rubygem_version(url: ParseResult) -> Optional[str]:
    if url.netloc != "rubygems.org":
        return None
    parts = url.path.split("/")
    gem = parts[-1]
    gem_name, rest = gem.rsplit("-")
    versions_url = f"https://rubygems.org/api/v1/versions/{gem_name}.json"
    info(f"fetch {versions_url}")
    resp = urllib.request.urlopen(versions_url)
    versions = json.load(resp)
    if len(versions) == 0:
        raise VersionError("No versions found")
    for version in versions:
        if not version["prerelease"]:
            number = version["number"]
            assert isinstance(number, str)
            return number
    number = versions[0]["number"]
    assert isinstance(number, str)
    return number
