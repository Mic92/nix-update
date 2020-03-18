import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, ParseResult
import json
import re

from .errors import VersionError
from .utils import info


def fetch_latest_github_version(url: ParseResult) -> str:
    parts = url.path.split("/")
    owner, repo = parts[1], parts[2]
    repo = re.sub(r"\.git$", "", repo)
    # TODO fallback to tags?
    feed_url = f"https://github.com/{owner}/{repo}/releases.atom"
    info(f"fetch {feed_url}")
    resp = urllib.request.urlopen(feed_url)
    tree = ET.fromstring(resp.read())
    release = tree.find(".//{http://www.w3.org/2005/Atom}entry")
    if release is None:
        raise VersionError("No release found")
    link = release.find("{http://www.w3.org/2005/Atom}link")
    assert link is not None
    href = link.attrib["href"]
    url = urlparse(href)
    return url.path.split("/")[-1]


def fetch_latest_pypi_version(url: ParseResult) -> str:
    parts = url.path.split("/")
    package = parts[2]
    pypi_url = f"https://pypi.org/pypi/{package}/json"
    info(f"fetch {pypi_url}")
    resp = urllib.request.urlopen(pypi_url)
    data = json.loads(resp.read())
    return data["info"]["version"]


def fetch_latest_gitlab_version(url: ParseResult) -> str:
    parts = url.path.split("/")
    project_id = parts[4]
    gitlab_url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/tags"
    info(f"fetch {gitlab_url}")
    resp = urllib.request.urlopen(gitlab_url)
    data = json.loads(resp.read())
    if len(data) == 0:
        raise VersionError("No git tags found")
    return data[0]["name"]


# def find_repology_release(attr) -> str:
#    resp = urllib.request.urlopen(f"https://repology.org/api/v1/projects/{attr}/")
#    data = json.loads(resp.read())
#    for name, pkg in data.items():
#        for repo in pkg:
#            if repo["status"] == "newest":
#                return repo["version"]
#    return None


def fetch_latest_version(url_str: str) -> str:
    url = urlparse(url_str)

    if url.netloc == "pypi":
        return fetch_latest_pypi_version(url)
    elif url.netloc == "github.com":
        return fetch_latest_github_version(url)
    elif url.netloc == "gitlab.com":
        return fetch_latest_gitlab_version(url)
    else:
        raise VersionError(
            "Please specify the version. We can only get the latest version from github/pypi projects right now"
        )
