import json
import re
import urllib.request
from datetime import datetime
from urllib.parse import ParseResult, quote_plus

from nix_update.errors import VersionError
from nix_update.utils import info

from .version import Version

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
    resp = urllib.request.urlopen(gitlab_url)
    json_tags = json.loads(resp.read())
    if len(json_tags) == 0:
        msg = "No git tags found"
        raise VersionError(msg)
    releases = []
    tags = []
    for tag in json_tags:
        name = tag["name"]
        assert isinstance(name, str)
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
    resp = urllib.request.urlopen(gitlab_url)
    commits = json.load(resp)

    try:
        versions = fetch_gitlab_versions(url)
    except VersionError:
        versions = []
    latest_version = versions[0].number if versions else "0"

    for commit in commits:
        commit_date = datetime.strptime(
            commit["committed_date"],
            "%Y-%m-%dT%H:%M:%S.000%z",
        )
        commit_date -= commit_date.utcoffset()  # type: ignore[operator]
        date = commit_date.strftime("%Y-%m-%d")
        return [Version(f"{latest_version}-unstable-{date}", rev=commit["id"])]
    return []
