import json
import urllib.request
from typing import Optional
from urllib.parse import ParseResult

from ..utils import extract_version, info, version_is_stable


def fetch_pypi_version(
    url: ParseResult, version_regex: str, unstable_version: bool
) -> Optional[str]:
    if url.netloc != "pypi":
        return None
    parts = url.path.split("/")
    package = parts[2]
    pypi_url = f"https://pypi.org/pypi/{package}/json"
    info(f"fetch {pypi_url}")
    resp = urllib.request.urlopen(pypi_url)
    data = json.loads(resp.read())
    version = data["info"]["version"]
    assert isinstance(version, str)
    extracted = extract_version(version, version_regex)
    if extracted is not None and (unstable_version or version_is_stable(extracted)):
        return extracted

    return None
