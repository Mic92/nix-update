#!/usr/bin/env python3
import unittest.mock
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urlparse

import conftest

from nix_update.version import fetch_latest_version
from nix_update.version.version import VersionPreference

TEST_ROOT = Path(__file__).parent.resolve()


def fake_urlopen(url: str) -> BinaryIO:
    del url
    return open(TEST_ROOT.joinpath("test_branch.atom"), "rb")


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
            == "unstable-2021-12-13"
        )
