import json
import urllib.request
from urllib.parse import ParseResult

from nix_update.utils import info

from .version import Version


def fetch_pypi_versions(url: ParseResult, quiet: bool) -> list[Version]:
    if url.netloc != "pypi":
        return []
    parts = url.path.split("/")
    package = parts[2]
    pypi_url = f"https://pypi.org/pypi/{package}/json"
    info(f"fetch {pypi_url}", quiet)
    resp = urllib.request.urlopen(pypi_url)
    data = json.loads(resp.read())
    version = data["info"]["version"]
    assert isinstance(version, str)
    # TODO look at info->releases instead
    return [Version(version)]
