from __future__ import annotations

import io
import subprocess
import unittest.mock
import urllib.error
import urllib.request
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

from nix_update.options import Options
from nix_update.update import update
from nix_update.version import VersionFetchConfig, fetch_latest_version
from nix_update.version.pecl import fetch_pecl_versions
from nix_update.version.version import Version, VersionPreference

if TYPE_CHECKING:
    from pathlib import Path

PDO_SQLSRV_RELEASES = b"""<?xml version="1.0" encoding="UTF-8" ?>
<a xmlns="http://pear.php.net/dtd/rest.allreleases"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink"     xsi:schemaLocation="http://pear.php.net/dtd/rest.allreleases
    http://pear.php.net/dtd/rest.allreleases.xsd">
 <p>pdo_sqlsrv</p>
 <c>pecl.php.net</c>
 <r><v>5.14.0beta1</v><s>beta</s></r>
 <r><v>5.13.4RC1</v><s>stable</s></r>
 <r><v>5.13.4dev</v><s>stable</s></r>
 <r><v>5.13.3</v><s>stable</s></r>
 <r><v>5.13.2</v><s>stable</s></r>
 <r><v>5.13.0beta1</v><s>beta</s></r>
</a>
"""


def fake_pecl_urlopen(url: str, timeout: float | None = None) -> io.BytesIO:
    del timeout  # Unused in test
    if url == "https://pecl.php.net/rest/r/pdo_sqlsrv/allreleases.xml":
        return io.BytesIO(PDO_SQLSRV_RELEASES)
    raise ValueError(f"Unexpected URL in test: {url}")  # noqa: EM102, TRY003


def latest(url: str, preference: VersionPreference) -> str:
    with unittest.mock.patch("urllib.request.urlopen", fake_pecl_urlopen):
        return fetch_latest_version(
            urlparse(url),
            VersionFetchConfig(preference=preference, version_regex="(.*)"),
        ).number


def test_stable_skips_mislabelled_prereleases() -> None:
    versions = {
        v.number: v.prerelease
        for v in fetch_pecl_versions_mocked(
            "https://pecl.php.net/get/pdo_sqlsrv-5.13.2.tgz"
        )
    }
    assert versions["5.13.4RC1"] is True
    assert versions["5.13.4dev"] is True
    assert versions["5.13.3"] is False


def fetch_pecl_versions_mocked(url: str) -> list[Version]:
    with unittest.mock.patch("urllib.request.urlopen", fake_pecl_urlopen):
        return fetch_pecl_versions(urlparse(url))


def test_stable_skips_beta() -> None:
    url = "https://pecl.php.net/get/pdo_sqlsrv-5.13.2.tgz"
    assert latest(url, VersionPreference.STABLE) == "5.13.3"


def test_unstable_picks_beta() -> None:
    url = "https://pecl.php.net/get/pdo_sqlsrv-5.13.2.tgz"
    assert latest(url, VersionPreference.UNSTABLE) == "5.14.0beta1"


def test_mixed_case_name() -> None:
    url = "https://pecl.php.net/get/PDO_SQLSRV-5.13.2.tgz"
    assert latest(url, VersionPreference.STABLE) == "5.13.3"


def test_ignores_other_urls() -> None:
    for url in (
        "https://pypi.org/packages/source/p/pdo_sqlsrv/pdo_sqlsrv-5.13.2.tar.gz",
        "https://pecl.php.net/package/pdo_sqlsrv",
    ):
        assert fetch_pecl_versions(urlparse(url)) == []


def test_update(testpkgs: Path) -> None:
    try:
        response = urllib.request.urlopen(
            "https://pecl.php.net/rest/r/yaml/allreleases.xml",
            timeout=5,
        )
        response.read()
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        pytest.xfail("PECL is taking too long to respond")

    opts = Options(attribute="pecl", import_path=str(testpkgs))
    update(opts)
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs,
            "pecl.version",
        ],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    assert tuple(map(int, version.split("."))) >= (2, 3, 0)
