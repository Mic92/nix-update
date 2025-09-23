from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


def test_scoped_package_update(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "npm-scoped"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "npm-scoped.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "show"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(commit)
    # Check that version was updated
    assert version != "1.10.2"
    assert version in commit
    # Check that the diff URL is properly formatted with URL-encoded scope
    assert "https://npmdiff.dev/@motesoftware%2Fnanocoder/1.10.2/" in commit
