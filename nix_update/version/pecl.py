from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from nix_update.utils import info

from .http import DEFAULT_TIMEOUT
from .version import Version

if TYPE_CHECKING:
    from urllib.parse import ParseResult
    from xml.etree.ElementTree import Element

# https://pecl.php.net/get/<name>-<version>.tgz
# Name may contain underscores (pdo_sqlsrv), so the version is everything after
# the last dash.
filename_regex = re.compile(r"^/get/([^/]+)-[^-/]+\.(?:tgz|tar(?:\.[^./]+)?)$")

namespace = {"pecl": "http://pear.php.net/dtd/rest.allreleases"}

# PECL's stability field is not always accurate (e.g. igbinary 3.2.17RC1 is
# published as "stable"), so also check for PHP's pre-release version suffixes.
unstable_regex = re.compile(r"(?:dev|alpha|beta|rc)\d*$", re.IGNORECASE)


def version_from_release(r: Element) -> Version | None:
    number = r.findtext("pecl:v", namespaces=namespace)
    if not number:
        return None
    stability = r.findtext("pecl:s", namespaces=namespace)
    prerelease = stability != "stable" or unstable_regex.search(number) is not None
    return Version(number, prerelease=prerelease)


def fetch_pecl_versions(url: ParseResult) -> list[Version]:
    if url.netloc != "pecl.php.net":
        return []
    m = filename_regex.match(url.path)
    if not m:
        return []
    # The REST API handles only lowercase package names.
    pname = m[1].lower()
    releases_url = f"https://pecl.php.net/rest/r/{pname}/allreleases.xml"
    info(f"fetch {releases_url}")
    with urllib.request.urlopen(releases_url, timeout=DEFAULT_TIMEOUT) as resp:
        tree = ET.fromstring(resp.read())

    versions = []
    for r in tree.findall("pecl:r", namespace):
        version = version_from_release(r)
        if version:
            versions.append(version)
    return versions
