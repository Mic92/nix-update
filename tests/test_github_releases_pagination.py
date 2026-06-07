from __future__ import annotations

import json
import unittest.mock
from io import BytesIO
from typing import TYPE_CHECKING, BinaryIO
from urllib.parse import parse_qs, urlparse

from nix_update.version import VersionFetchConfig, fetch_latest_version
from nix_update.version.version import VersionPreference

if TYPE_CHECKING:
    from urllib.request import Request

    from tests import conftest

# Page 1 contains only prereleases, the stable release is on page 2.
PAGES = {
    1: [{"tag_name": f"v1.6.6-rc.{n}", "prerelease": True} for n in range(154, 54, -1)],
    2: [{"tag_name": "v1.6.5", "prerelease": False}],
}


def test_paginates_past_prerelease_only_page(helpers: conftest.Helpers) -> None:
    del helpers
    requests: list[str] = []

    def fake_urlopen(req: Request, timeout: float | None = None) -> BinaryIO:
        del timeout  # Unused in test
        requests.append(req.get_full_url())
        page = int(parse_qs(urlparse(req.get_full_url()).query)["page"][0])
        return BytesIO(json.dumps(PAGES.get(page, [])).encode())

    with unittest.mock.patch("urllib.request.urlopen", fake_urlopen):
        version = fetch_latest_version(
            urlparse("https://github.com/abhigyanpatwari/GitNexus"),
            VersionFetchConfig(
                preference=VersionPreference.STABLE,
                version_regex="v(.*)",
                fetcher_args={"use_github_releases": True},
            ),
        )
    assert version.number == "1.6.5"
    # Page 2 is short, so pagination stops before the cap.
    assert len(requests) == len(PAGES)


def test_releases_limit(helpers: conftest.Helpers) -> None:
    del helpers
    requests: list[str] = []

    def fake_urlopen(req: Request, timeout: float | None = None) -> BinaryIO:
        del timeout  # Unused in test
        requests.append(req.get_full_url())
        page = int(parse_qs(urlparse(req.get_full_url()).query)["page"][0])
        return BytesIO(json.dumps(PAGES.get(page, [])).encode())

    with unittest.mock.patch("urllib.request.urlopen", fake_urlopen):
        version = fetch_latest_version(
            urlparse("https://github.com/abhigyanpatwari/GitNexus"),
            VersionFetchConfig(
                preference=VersionPreference.UNSTABLE,
                version_regex="v(.*)",
                fetcher_args={
                    "use_github_releases": True,
                    "github_releases_limit": 100,
                },
            ),
        )
    assert version.number == "1.6.6-rc.154"
    assert len(requests) == 1
