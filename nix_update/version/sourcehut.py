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
    link = entry.find("link")
    assert link is not None
    url = urlparse(str(link.text))
    return Version(url.path.split("/")[-1])


def fetch_sourcehut_versions(url: ParseResult) -> List[Version]:
    if url.netloc != "git.sr.ht":
        return []
    parts = url.path.split("/")
    owner, repo = parts[1], parts[2]
    # repo = re.sub(r"\.git$", "", repo)
    feed_url = f"https://git.sr.ht/{owner}/{repo}/refs/rss.xml"
    info(f"fetch {feed_url}")
    resp = urllib.request.urlopen(feed_url)
    tree = ET.fromstring(resp.read())
    releases = tree.findall(".//item")
    return [version_from_entry(x) for x in releases]
