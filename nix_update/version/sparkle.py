from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from nix_update.utils import info

from .http import DEFAULT_TIMEOUT, urlopen

if TYPE_CHECKING:
    from urllib.parse import ParseResult

    from .version import Version


def fetch_sparkle_versions(url: ParseResult) -> list[Version]:
    # https://fork.dev/update/feed-stable.xml
    # if the URL isn't an xml document, it can't be sparkle
    if not url.path.endswith(".xml"):
        return []

    with urlopen(url.geturl(), timeout=DEFAULT_TIMEOUT) as resp:
        xml = resp.read()
        info(f"xml: {xml}")
    tree = ET.fromstring(xml)

    # tree.findall("enclosure").sort(key=lambda enc: enc.attrib["sparkle:version"])
    versions = tree.findall(".//channel/item/enclosure")
    info(versions)
    # for enclosure in tree.findall("enclosure"):

    return [versions[0].attrib["sparkle:version"]]
