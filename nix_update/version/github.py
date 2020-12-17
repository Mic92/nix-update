import re
import urllib.request
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from typing import Optional
from urllib.parse import ParseResult, urlparse

from ..errors import VersionError
from ..utils import extract_version, info


def version_from_entry(entry: Element) -> Optional[str]:
    if entry is None:
        raise VersionError("No release found")
    link = entry.find("{http://www.w3.org/2005/Atom}link")
    assert link is not None
    href = link.attrib["href"]
    url = urlparse(href)
    return url.path.split("/")[-1]


def fetch_github_version(url: ParseResult, version_regex: str) -> Optional[str]:
    if url.netloc != "github.com":
        return None
    parts = url.path.split("/")
    owner, repo = parts[1], parts[2]
    repo = re.sub(r"\.git$", "", repo)
    # TODO fallback to tags?
    feed_url = f"https://github.com/{owner}/{repo}/releases.atom"
    info(f"fetch {feed_url}")
    resp = urllib.request.urlopen(feed_url)
    tree = ET.fromstring(resp.read())
    releases = tree.findall(".//{http://www.w3.org/2005/Atom}entry")
    entries = [version_from_entry(x) for x in releases]
    filtered = [
        x for x in entries if x is not None and extract_version(x, version_regex)
    ]

    return filtered[0]
