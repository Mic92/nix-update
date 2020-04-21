import json
import re
import urllib.request
from typing import Optional
from urllib.parse import ParseResult

from ..errors import VersionError
from ..utils import info

GITLAB_API = re.compile(
    r"http(s)?://(?P<site>[^/]+)/api/v4/projects/(?P<project_id>[^/]*)/repository/archive.tar.gz\?sha=(?P<version>.+)"
)


def fetch_gitlab_version(url: ParseResult) -> Optional[str]:
    match = GITLAB_API.match(url.geturl())
    if not match:
        return None
    domain = match.group("domain")
    project_id = match.group("project_id")
    gitlab_url = f"https://{domain}/api/v4/projects/{project_id}/repository/tags"
    info(f"fetch {gitlab_url}")
    resp = urllib.request.urlopen(gitlab_url)
    tags = json.loads(resp.read())
    if len(tags) == 0:
        raise VersionError("No git tags found")
    for tag in tags:
        if tag["release"]:
            return tag["name"]
    # if no release is found, use latest tag
    return tags[0]["name"]
