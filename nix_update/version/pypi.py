import json
import urllib.request
from typing import List
from urllib.parse import ParseResult

from .version import Version
from ..utils import info


def fetch_pypi_versions(url: ParseResult) -> List[Version]:
    if url.netloc != "pypi":
        return []
    parts = url.path.split("/")
    package = parts[2]
    pypi_url = f"https://pypi.org/pypi/{package}/json"
    info(f"fetch {pypi_url}")
    resp = urllib.request.urlopen(pypi_url)
    data = json.loads(resp.read())
    version = data["info"]["version"]
    assert isinstance(version, str)
    # TODO look at info->releases instead
    return [Version(version)]
