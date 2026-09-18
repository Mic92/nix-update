from __future__ import annotations

import re
from datetime import UTC, datetime
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any
from urllib.error import URLError

from nix_update.errors import VersionError

from .http import fetch_json
from .version import Version

if TYPE_CHECKING:
    from urllib.parse import ParseResult

KNOWN_RADICLE_HOSTS = [
    "seed.radicle.dev",
    "iris.radicle.network",
    "rosa.radicle.network",
]


def is_radicle_host(host: str) -> bool:
    if host in KNOWN_RADICLE_HOSTS:
        return True

    try:
        resp = fetch_json(f"https://{host}/api/v1")
    except (URLError, JSONDecodeError):
        return False

    return isinstance(resp, dict) and resp.get("service") == "radicle-httpd"


def extract_rid(path: str) -> str | None:
    if not (m := re.match(r"/(rad:)?(z[1-9A-HJ-NP-Za-km-z]{20,28})(\.git)?$", path)):
        return None
    return m[2]


def fetch_radicle_versions(
    url: ParseResult, extra_args: dict[str, Any] | None = None
) -> list[Version]:
    if not is_radicle_host(url.netloc):
        return []

    if not (rid := extract_rid(url.path)):
        return []

    tags = (
        fetch_json(f"https://{url.netloc}/api/v1/repos/{rid}/remotes/{nid}")["refs"]
        if extra_args and (nid := extra_args["radicle_namespace"])
        else fetch_json(f"https://{url.netloc}/api/v1/repos/{rid}")["refs"]["tags"]
    )

    prefix = "refs/tags/"
    return [Version(tag.removeprefix(prefix)) for tag in tags if tag.startswith(prefix)]


def fetch_radicle_snapshots(
    url: ParseResult, branch: str, extra_args: dict[str, Any] | None = None
) -> list[Version]:
    if not is_radicle_host(url.netloc):
        return []

    if not (rid := extract_rid(url.path)):
        return []

    if extra_args and extra_args["radicle_namespace"]:
        msg = "`--version=branch` is only supported for branches in the canonical namespace"
        raise VersionError(msg)

    repo = fetch_json(f"https://{url.netloc}/api/v1/repos/{rid}")
    if branch == "HEAD":
        branch = repo["payloads"]["xyz.radicle.project"]["data"]["defaultBranch"]

    commit_sha = repo["refs"]["refs"][f"refs/heads/{branch}"]
    commit = fetch_json(
        f"https://{url.netloc}/api/v1/repos/{rid}/commits?parent={commit_sha}&perPage=1"
    )[0]

    if versions := repo["refs"]["tags"]:
        latest_version = max(
            versions.items(), key=lambda x: x[1]["tagger"]["timestamp"]
        )[0].removeprefix("refs/tags/")
    else:
        latest_version = "0"

    date = datetime.fromtimestamp(commit["committer"]["time"], UTC).date().isoformat()
    return [Version(f"{latest_version}-unstable-{date}", rev=commit_sha)]
