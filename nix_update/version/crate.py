import json
import urllib.request
from urllib.parse import ParseResult

from nix_update.utils import info

from .version import Version


def fetch_crate_versions(url: ParseResult) -> list[Version]:
    if url.netloc != "crates.io":
        return []
    parts = url.path.split("/")
    package = parts[4]
    crate_url = f"https://crates.io/api/v1/crates/{package}/versions"
    info(f"fetch {crate_url}")
    resp = urllib.request.urlopen(crate_url)
    data = json.loads(resp.read())
    return [
        Version(version["num"]) for version in data["versions"] if not version["yanked"]
    ]
