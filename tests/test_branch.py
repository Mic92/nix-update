import unittest.mock
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urlparse
from urllib.request import Request

from nix_update.version import fetch_latest_version
from nix_update.version.version import VersionPreference
from tests import conftest

TEST_ROOT = Path(__file__).parent.resolve()


def fake_urlopen(req: Request) -> BinaryIO:
    url = req.get_full_url()
    if url.endswith("releases.atom"):
        return TEST_ROOT.joinpath("test_branch_releases.atom").open("rb")
    return TEST_ROOT.joinpath("test_branch_commits_master.atom").open("rb")


def test_branch(helpers: conftest.Helpers) -> None:
    del helpers
    with unittest.mock.patch("urllib.request.urlopen", fake_urlopen):
        assert (
            fetch_latest_version(
                urlparse("https://github.com/Mic92/nix-update"),
                VersionPreference.BRANCH,
                "(.*)",
                "master",
            ).number
            == "1.2.0-unstable-2024-02-19"
        )
