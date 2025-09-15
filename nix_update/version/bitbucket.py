from __future__ import annotations

from typing import TYPE_CHECKING

from .http import fetch_json
from .version import Version

if TYPE_CHECKING:
    from urllib.parse import ParseResult


def fetch_bitbucket_versions(url: ParseResult) -> list[Version]:
    if url.netloc not in ["bitbucket.org", "bitbucket.io"]:
        return []

    _, owner, repo, *_ = url.path.split("/")
    # paging controlled by pagelen parameter, by default it is 10
    tags_url = f"https://{url.netloc}/!api/2.0/repositories/{owner}/{repo}/refs/tags?sort=-target.date"
    tags = fetch_json(tags_url)["values"]
    return [Version(tag["name"]) for tag in tags]


def fetch_bitbucket_snapshots(url: ParseResult, branch: str) -> list[Version]:
    if url.netloc not in ["bitbucket.org", "bitbucket.io"]:
        return []

    _, owner, repo, *_ = url.path.split("/")
    # seems to ignore pagelen parameter (always returns one entry)
    commits_url = f'https://{url.netloc}/!api/2.0/repositories/{owner}/{repo}/refs?q=name="{branch}"'
    ref = fetch_json(commits_url)["values"][0]["target"]

    versions = fetch_bitbucket_versions(url)
    latest_version = versions[0].number if versions else "0"

    date = ref["date"][:10]  # to YYYY-MM-DD
    return [Version(f"{latest_version}-unstable-{date}", rev=ref["hash"])]
