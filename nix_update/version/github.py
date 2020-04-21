import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import ParseResult, urlparse

from ..errors import VersionError
from ..utils import info


def fetch_github_version(url: ParseResult) -> Optional[str]:
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
    release = tree.find(".//{http://www.w3.org/2005/Atom}entry")
    if release is None:
        raise VersionError("No release found")
    link = release.find("{http://www.w3.org/2005/Atom}link")
    assert link is not None
    href = link.attrib["href"]
    url = urlparse(href)
    return url.path.split("/")[-1]
