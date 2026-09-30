from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from nix_update.errors import VersionError

from .http import fetch_json
from .version import Version

if TYPE_CHECKING:
    from urllib.parse import ParseResult


def repo_api_url(url: ParseResult, extra_args: dict[str, Any] | None) -> str | None:
    """Return the radicle-httpd API URL if the source uses fetchFromRadicle."""
    # fetchFromRadicle derives the url from `seed`, so netloc is the seed.
    if not extra_args or not (repo := extra_args.get("radicle_repo")):
        return None
    return f"https://{url.netloc}/api/v1/repos/{repo}"


def fetch_radicle_versions(
    url: ParseResult, extra_args: dict[str, Any] | None = None
) -> list[Version]:
    if not (api := repo_api_url(url, extra_args)):
        return []

    if nid := (extra_args or {}).get("radicle_namespace"):
        tags = fetch_json(f"{api}/remotes/{nid}")["refs"]
    else:
        tags = fetch_json(api)["refs"]["tags"]

    prefix = "refs/tags/"
    return [Version(t.removeprefix(prefix)) for t in tags if t.startswith(prefix)]


def fetch_radicle_snapshots(
    url: ParseResult, branch: str, extra_args: dict[str, Any] | None = None
) -> list[Version]:
    if not (api := repo_api_url(url, extra_args)):
        return []

    if (extra_args or {}).get("radicle_namespace"):
        msg = "`--version=branch` is only supported for branches in the canonical namespace"
        raise VersionError(msg)

    repo = fetch_json(api)
    if branch == "HEAD":
        branch = repo["payloads"]["xyz.radicle.project"]["data"]["defaultBranch"]

    rev = repo["refs"]["refs"][f"refs/heads/{branch}"]
    commit = fetch_json(f"{api}/commits?parent={rev}&perPage=1")[0]
    date = datetime.fromtimestamp(commit["committer"]["time"], UTC).date()

    tags = repo["refs"]["tags"]
    base = (
        max(tags, key=lambda t: tags[t]["tagger"]["timestamp"]).removeprefix(
            "refs/tags/"
        )
        if tags
        else "0"
    )
    return [Version(f"{base}-unstable-{date}", rev=rev)]
