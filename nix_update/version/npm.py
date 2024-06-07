import json
import urllib.request
from urllib.parse import ParseResult

from ..utils import info
from .version import Version


def fetch_npm_versions(url: ParseResult) -> list[Version]:
    if url.netloc != "registry.npmjs.org":
        return []
    parts = url.path.split("/")
    package = parts[1]
    npm_url = f"https://registry.npmjs.org/{package}/latest"
    info(f"fetch {npm_url}")
    resp = urllib.request.urlopen(npm_url)
    data = json.loads(resp.read())
    return [Version(data["version"])]
