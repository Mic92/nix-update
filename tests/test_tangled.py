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

REPO = "https://tangled.org/did:plc:jj6ajj6duxnlthwtnob4qyuv"


def test_main(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "tangled"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "tangled.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    assert tuple(map(int, version.split("."))) >= (0, 9, 1)
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    assert version in commit
    assert "tangled" in commit
    assert f"{REPO}/compare/v0.8.0...v{version}" in commit


@pytest.mark.usefixtures("helpers")
def test_stable() -> None:
    version = fetch_latest_version(
        urlparse(f"{REPO}/archive/refs/tags/v0.8.0"),
        VersionFetchConfig(VersionPreference.STABLE, "v(.*)", old_rev_tag="v0.8.0"),
    )
    assert tuple(map(int, version.number.split("."))) >= (0, 9, 1)


@pytest.mark.usefixtures("helpers")
def test_branch() -> None:
    config = VersionFetchConfig(
        preference=VersionPreference.BRANCH,
        version_regex="v(.*)",
        branch="main",
    )
    version = fetch_latest_version(urlparse(REPO), config)
    assert version.rev is not None
    assert date.fromisoformat(version.number[-10:]) >= date(2026, 11, 26)
