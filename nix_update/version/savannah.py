from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING
from urllib.parse import ParseResult, urljoin, urlparse

from nix_update.utils import info

from .http import DEFAULT_TIMEOUT
from .version import Version

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

filename_regex = re.compile(r"-(\d+(?:\.\d+)*(?:-[^-.]+)?)\.tar\.[^.]+$")


def version_from_link(a: Element, baseurl: str) -> Version | None:
    try:
        href = a.attrib["href"]
    except KeyError:
        return None
    url = urlparse(urljoin(baseurl, href))
    m = filename_regex.search(url.path)
    if not m:
        return None
    return Version(m[1])


def fetch_savannah_versions(url: ParseResult) -> list[Version]:
    if url.scheme != "mirror" or url.netloc != "savannah":
        return []
    pname = url.path.split("/", 2)[1]
    dir_url = f"https://download.savannah.nongnu.org/releases/{pname}/?C=M&O=D"
    info(f"fetch {dir_url}")
    with urllib.request.urlopen(dir_url, timeout=DEFAULT_TIMEOUT) as resp:
        html = resp.read()

    # only parse tbody
    start = html.index(b"<tbody>")
    end = html.index(b"</tbody>", start) + 8
    tree = ET.fromstring(html[start:end])

    versions = []
    for a in tree.findall(".//a"):
        version = version_from_link(a, dir_url)
        if version:
            versions.append(version)
    return versions
