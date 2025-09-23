from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import main

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
