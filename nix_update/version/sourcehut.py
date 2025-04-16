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


def snapshot_from_entry(entry: Element, url: ParseResult, quiet: bool) -> Version:
    versions = fetch_sourcehut_versions(url, quiet)
    latest_version = versions[0].number if versions else "0"
    pub_date = entry.find("pubDate")
    date = parsedate_to_datetime(pub_date.text).date()
    date_str = date.isoformat()
    rev = entry.find("link").text.split("/")[-1]
    return Version(f"{latest_version}-unstable-{date_str}", rev=rev)


def fetch_sourcehut_versions(url: ParseResult, quiet: bool) -> list[Version]:
    if url.netloc != "git.sr.ht":
        return []
    parts = url.path.split("/")
    owner, repo = parts[1], parts[2]
    # repo = re.sub(r"\.git$", "", repo)
    feed_url = f"https://git.sr.ht/{owner}/{repo}/refs/rss.xml"
    info(f"fetch {feed_url}", quiet)
    resp = urllib.request.urlopen(feed_url)
    tree = ET.fromstring(resp.read())
    releases = tree.findall(".//item")
    return [version_from_entry(x) for x in releases]


def fetch_sourcehut_snapshots(
    url: ParseResult, branch: str, quiet: bool
) -> list[Version]:
    if url.netloc != "git.sr.ht":
        return []
    parts = url.path.split("/")
    owner, repo = parts[1], parts[2]
    feed_url = f"https://git.sr.ht/{owner}/{repo}/log/{branch}/rss.xml"
    info(f"fetch {feed_url}", quiet)
    resp = urllib.request.urlopen(feed_url)
    tree = ET.fromstring(resp.read())
    latest_commit = tree.find(".//item")
    return [snapshot_from_entry(latest_commit, url, quiet)]
