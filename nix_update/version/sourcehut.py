import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import ParseResult, urlparse
from xml.etree.ElementTree import Element

from nix_update.errors import VersionError
from nix_update.utils import info

from .version import Version


def version_from_entry(entry: Element) -> Version:
    if entry is None:
        msg = "No release found"
        raise VersionError(msg)
    link = entry.find("link")
    assert link is not None
    url = urlparse(str(link.text))
    return Version(url.path.split("/")[-1])


def snapshot_from_entry(entry: Element, url: ParseResult) -> Version:
    versions = fetch_sourcehut_versions(url)
    latest_version = versions[0].number if versions else "0"
    pub_date = entry.find("pubDate")
    if pub_date is None:
        raise VersionError("No pubDate found in atom feed {url}")
    parsed = parsedate_to_datetime(pub_date.text)
    if parsed is None:
        raise VersionError(f"Invalid pubDate format: {pub_date.text}")
    date = parsed.date()
    date_str = date.isoformat()
    node = entry.find("link")
    if node is None or node.text is None:
        raise VersionError("No link found in atom feed {url}")
    rev = node.text.split("/")[-1]
    return Version(f"{latest_version}-unstable-{date_str}", rev=rev)


def fetch_sourcehut_versions(url: ParseResult) -> list[Version]:
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


def fetch_sourcehut_snapshots(url: ParseResult, branch: str) -> list[Version]:
    if url.netloc != "git.sr.ht":
        return []
    parts = url.path.split("/")
    owner, repo = parts[1], parts[2]
    feed_url = f"https://git.sr.ht/{owner}/{repo}/log/{branch}/rss.xml"
    info(f"fetch {feed_url}")
    resp = urllib.request.urlopen(feed_url)
    tree = ET.fromstring(resp.read())
    latest_commit = tree.find(".//item")
    if latest_commit is None:
        msg = f"No commit found in atom feed {url}"
        raise VersionError(msg)
    return [snapshot_from_entry(latest_commit, url)]
