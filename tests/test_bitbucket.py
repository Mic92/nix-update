from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


# integration test for bitbucket versions (fetch_bitbucket_versions), mostly
# copied from test_gitea.py.
# run directly with 'nix develop -c pytest -s ./tests/test_bitbucket.py'.
def test_version(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "bitbucket"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "bitbucket.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    assert tuple(map(int, version.split("."))) > (1, 0)
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(commit)
    assert version in commit
    assert "bitbucket" in commit
    assert "/nielsenb/aniso8601/branches/compare/" in commit
    assert "%0Dv9.0.0" in commit


# integration test for bitbucket snapshots
def test_snapshot(testpkgs_git: Path) -> None:
    main(
        [
            "--file",
            str(testpkgs_git),
            "--commit",
            "--version=branch=master",
            "bitbucket-snapshot",
        ],
    )
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "bitbucket-snapshot.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(commit)
    assert version in commit
    assert "bitbucket" in commit
    assert "/nielsenb/aniso8601/branches/compare/" in commit
    assert "%0D55b1b849a57341a303ae47eb67c7ecf8c283b7f8" in commit
