import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import ParseResult, unquote, urlparse
from xml.etree.ElementTree import Element

from ..errors import VersionError
from ..utils import info, warn
from .version import Version


def version_from_entry(entry: Element) -> Version:
    if entry is None:
        raise VersionError("No release found")
    link = entry.find("{http://www.w3.org/2005/Atom}link")
    assert link is not None
    href = link.attrib["href"]
    url = urlparse(href)
    # TODO: set pre-release flag
    return Version(unquote(url.path.split("/")[-1]))


def fetch_github_versions(url: ParseResult) -> list[Version]:
    if url.netloc != "github.com":
        return []
    parts = url.path.split("/")
    owner, repo = parts[1], parts[2]
    repo = re.sub(r"\.git$", "", repo)
    github_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    token = os.environ.get("GITHUB_TOKEN")
    req = urllib.request.Request(
        github_url,
        headers={} if token is None else {"Authorization": f"Bearer {token}"},
    )
    try:
        info(f"trying to fetch {github_url}")
        resp = urllib.request.urlopen(req)
        releases = json.loads(resp.read())
        if releases:
            return [Version(x["tag_name"], x["prerelease"]) for x in releases]
        else:
            warn("No GitHub releases found, falling back to tags")
    except urllib.error.URLError as e:
        warn(
            f"Cannot fetch '{github_url}' using GitHub API ({e}), falling back to public atom feed"
        )
    feed_url = f"https://github.com/{owner}/{repo}/releases.atom"
    info(f"fetch {feed_url}")
    resp = urllib.request.urlopen(feed_url)
    tree = ET.fromstring(resp.read())
    releases = tree.findall(".//{http://www.w3.org/2005/Atom}entry")
    return [version_from_entry(x) for x in releases]


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
