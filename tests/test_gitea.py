from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from nix_update import main
from nix_update.version import VersionFetchConfig, fetch_latest_version
from nix_update.version.version import VersionPreference

if TYPE_CHECKING:
    from pathlib import Path

# Minimum expected gitea version for testing
MIN_GITEA_VERSION = 30


def test_main(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "gitea"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "gitea.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    assert int(version) >= MIN_GITEA_VERSION
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(commit)
    assert version in commit
    assert "gitea" in commit
    assert "https://codeberg.org/nsxiv/nsxiv/compare/v29...v" in commit


def test_tags_newer_than_releases() -> None:
    # Regression test for #636: emacs-reader tags 0.3.1/0.3.2 have no Gitea
    # release, so the GitHub-style releases.atom (which Codeberg also serves)
    # must not be consulted or nix-update downgrades to 0.3.0.
    url = urlparse(
        "https://codeberg.org/MonadicSheep/emacs-reader/archive/0.3.2.tar.gz",
    )
    version = fetch_latest_version(
        url,
        VersionFetchConfig(VersionPreference.STABLE, "(.*)", old_rev_tag="0.3.2"),
    )
    assert tuple(map(int, version.number.split("."))) >= (0, 3, 2)
