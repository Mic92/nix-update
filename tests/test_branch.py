import unittest.mock
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urlparse
from urllib.request import Request

from nix_update.version import VersionFetchConfig, fetch_latest_version
from nix_update.version.version import VersionPreference
from tests import conftest

TEST_ROOT = Path(__file__).parent.resolve()


def fake_urlopen(req: Request) -> BinaryIO:
    url = req.get_full_url()
    if url.endswith("releases.atom"):
        return TEST_ROOT.joinpath("test_branch_releases.atom").open("rb")
    if url.endswith("/releases?per_page=100"):
        return TEST_ROOT.joinpath("test_branch_releases.json").open("rb")
    return TEST_ROOT.joinpath("test_branch_commits_master.atom").open("rb")


def test_branch(helpers: conftest.Helpers) -> None:
    del helpers
    with unittest.mock.patch("urllib.request.urlopen", fake_urlopen):
        assert (
            fetch_latest_version(
                urlparse("https://github.com/Mic92/nix-update"),
                VersionFetchConfig(
                    preference=VersionPreference.BRANCH,
                    version_regex="(.*)",
                    branch="master",
                ),
            ).number
            == "1.2.0-unstable-2024-02-19"
        )


def test_branch_releases(helpers: conftest.Helpers) -> None:
    del helpers
    with unittest.mock.patch("urllib.request.urlopen", fake_urlopen):
        assert (
            fetch_latest_version(
                urlparse("https://github.com/Mic92/nix-update"),
                VersionFetchConfig(
                    preference=VersionPreference.BRANCH,
                    version_regex="(.*)",
                    branch="master",
                    fetcher_args={"use_github_releases": True},
                ),
            ).number
            == "1.2.0-unstable-2024-02-19"
        )
