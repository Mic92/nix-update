import json
import re
import urllib.request
from typing import List
from urllib.parse import ParseResult

from .version import Version
from ..errors import VersionError
from ..utils import info

GITLAB_API = re.compile(
    r"http(s)?://(?P<domain>[^/]+)/api/v4/projects/(?P<project_id>[^/]*)/repository/archive.tar.gz\?sha=(?P<version>.+)"
)


def fetch_gitlab_versions(url: ParseResult) -> List[Version]:
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
        raise VersionError("No git tags found")
    releases = []
    tags = []
    for tag in json_tags:
        name = tag["name"]
        assert isinstance(name, str)
        if tag["release"]:
            # TODO: has gitlab preleases?
            releases.append(Version(name))
        else:
            tags.append(Version(name))
    # if no release is found, use latest tag
    if releases == []:
        return tags
    return releases
