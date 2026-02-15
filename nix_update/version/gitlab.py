from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import ParseResult, quote_plus

from nix_update.errors import VersionError
from nix_update.utils import info

from .http import fetch_json
from .version import Commit, Version

GITLAB_API = re.compile(
    r"http(s)?://(?P<domain>[^/]+)/api/v4/projects/(?P<project_id>[^/]*)/repository/archive.tar.gz\?sha=(?P<version>.+)",
)


def fetch_gitlab_versions(url: ParseResult) -> list[Version]:
    match = GITLAB_API.match(url.geturl())
    if not match:
        return []
    domain = match.group("domain")
    project_id = match.group("project_id")
    gitlab_url = f"https://{domain}/api/v4/projects/{project_id}/repository/tags"
    info(f"fetch {gitlab_url}")
    json_tags = fetch_json(gitlab_url)
    if len(json_tags) == 0:
        msg = "No git tags found"
        raise VersionError(msg)
    releases = []
    tags = []
    for tag in json_tags:
        name = tag["name"]
        if not isinstance(name, str):
            msg = f"Expected tag name to be string, got {type(name)}"
            raise TypeError(msg)
        if tag.get("release"):
            # TODO: has gitlab preleases?
            releases.append(Version(name))
        else:
            tags.append(Version(name))
    # if no release is found, use latest tag
    if releases == []:
        return tags
    return releases


def fetch_gitlab_snapshots(url: ParseResult, branch: str) -> list[Version]:
    match = GITLAB_API.match(url.geturl())
    if not match:
        return []
    domain = match.group("domain")
    project_id = match.group("project_id")
    gitlab_url = f"https://{domain}/api/v4/projects/{project_id}/repository/commits?ref_name={quote_plus(branch)}"
    info(f"fetch {gitlab_url}")
    commits = fetch_json(gitlab_url)

    try:
        versions = fetch_gitlab_versions(url)
    except VersionError:
        versions = []
    latest_version = versions[0].number if versions else "0"

    for commit in commits:
        commit_date = datetime.fromisoformat(commit["committed_date"])
        date = commit_date.strftime("%Y-%m-%d")
        return [
            Version(
                f"{latest_version}-unstable-{date}",
                rev=commit["id"],
                commit=Commit(sha=commit["id"], date=commit_date),
            ),
        ]
    return []
