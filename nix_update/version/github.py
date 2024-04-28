import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import ParseResult, urlparse

from ..utils import info
from .version import Version


def fetch_github_versions(url: ParseResult) -> list[Version]:
    if url.netloc != "github.com":
        return []
    parts = url.path.split("/")
    owner, repo = parts[1], parts[2]
    repo = re.sub(r"\.git$", "", repo)
    # TODO fallback to tags?
    github_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    info(f"fetch {github_url}")
    resp = urllib.request.urlopen(github_url)
    releases = json.loads(resp.read())
    return [Version(x["tag_name"], x["prerelease"]) for x in releases]


def fetch_github_snapshots(url: ParseResult, branch: str) -> list[Version]:
    if url.netloc != "github.com":
        return []
    parts = url.path.split("/")
    owner, repo = parts[1], parts[2]
    repo = re.sub(r"\.git$", "", repo)
    feed_url = f"https://github.com/{owner}/{repo}/commits/{branch}.atom"
    info(f"fetch {feed_url}")
    resp = urllib.request.urlopen(feed_url)
    tree = ET.fromstring(resp.read())
    commits = tree.findall(".//{http://www.w3.org/2005/Atom}entry")

    versions = fetch_github_versions(url)
    latest_version = versions[0].number if versions else "0"

    for entry in commits:
        link = entry.find("{http://www.w3.org/2005/Atom}link")
        updated = entry.find("{http://www.w3.org/2005/Atom}updated")
        assert (
            link is not None and updated is not None and updated.text is not None
        ), "cannot parse ATOM feed"
        url = urlparse(link.attrib["href"])
        commit = url.path.rsplit("/", maxsplit=1)[-1]
        date = updated.text.split("T", maxsplit=1)[0]
        return [Version(f"{latest_version}-unstable-{date}", rev=commit)]

    return []
