from __future__ import annotations

import subprocess
from datetime import date
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

from nix_update import main
from nix_update.version import VersionFetchConfig, fetch_latest_version
from nix_update.version.version import VersionPreference

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("package", ["radicle", "radicle-namespace"])
def test_main(testpkgs_git: Path, package: str) -> None:
    main(["--file", str(testpkgs_git), "--commit", package])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            f"{package}.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    assert tuple(map(int, version.split("."))) > (1, 10, 2)
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(commit)
    assert version in commit
    assert package in commit


@pytest.mark.usefixtures("helpers")
def test_branch() -> None:
    config = VersionFetchConfig(
        preference=VersionPreference.BRANCH,
        version_regex="releases/(.*)",
        branch="master",
    )
    version = fetch_latest_version(
        urlparse("https://seed.radicle.dev/z3gqcJUoA1n9HaHKufZs5FCSGazv5.git"), config
    ).number
    version_date = date.fromisoformat(version[-10:])
    assert version_date >= date(2026, 9, 10)
