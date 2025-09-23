from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


def test_main(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "pypi"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "pypi.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    assert tuple(map(int, version.split("."))) >= (3, 0, 1)
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(commit)
    assert f"pypi: 2.0.0 -> {version}" in commit
    assert (
        f"https://github.com/Mic92/python-mpd2/blob/{version}/doc/changes.rst" in commit
    )
