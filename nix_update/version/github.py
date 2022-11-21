import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import List
from urllib.parse import ParseResult, urlparse
from xml.etree.ElementTree import Element

from ..errors import VersionError
from ..utils import info
from .version import Version


def version_from_entry(entry: Element) -> Version:
    if entry is None:
        raise VersionError("No release found")
    link = entry.find("{http://www.w3.org/2005/Atom}link")
    assert link is not None
    href = link.attrib["href"]
    url = urlparse(href)
    # TODO: set pre-release flag
    return Version(url.path.split("/")[-1])


def fetch_github_versions(url: ParseResult) -> List[Version]:
    if url.netloc != "github.com":
        return []
    parts = url.path.split("/")
    owner, repo = parts[1], parts[2]
    repo = re.sub(r"\.git$", "", repo)
    # TODO fallback to tags?
    feed_url = f"https://github.com/{owner}/{repo}/releases.atom"
    info(f"fetch {feed_url}")
    resp = urllib.request.urlopen(feed_url)
    tree = ET.fromstring(resp.read())
    releases = tree.findall(".//{http://www.w3.org/2005/Atom}entry")
    return [version_from_entry(x) for x in releases]


def fetch_github_snapshots(url: ParseResult, branch: str) -> List[Version]:
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

    for entry in commits:
        link = entry.find("{http://www.w3.org/2005/Atom}link")
        updated = entry.find("{http://www.w3.org/2005/Atom}updated")
        assert (
            link is not None and updated is not None and updated.text is not None
        ), "cannot parse ATOM feed"
        url = urlparse(link.attrib["href"])
        commit = url.path.rsplit("/", maxsplit=1)[-1]
        date = updated.text.split("T", maxsplit=1)[0]
        return [Version(f"unstable-{date}", rev=commit)]

    return []
