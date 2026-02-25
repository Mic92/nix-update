from __future__ import annotations

import subprocess
from datetime import date
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

from nix_update.options import Options
from nix_update.update import update_package
from nix_update.version import (
    VersionFetchConfig,
    VersionPreference,
    fetch_latest_version,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_update(testpkgs: Path) -> None:
    opts = Options(attribute="sourcehut", import_path=str(testpkgs))
    update_package(opts)
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs,
            "sourcehut.version",
        ],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    assert tuple(map(int, version.split("."))) >= (0, 3, 6)


@pytest.mark.usefixtures("helpers")
def test_branch() -> None:
    config = VersionFetchConfig(
        preference=VersionPreference.BRANCH,
        version_regex="(.*)",
        branch="master",
    )
    version = fetch_latest_version(
        urlparse("https://git.sr.ht/~jcc/addr-book-combine"),
        config,
    ).number
    version_date = date.fromisoformat(version[-10:])
    assert version_date >= date(2022, 12, 14)
