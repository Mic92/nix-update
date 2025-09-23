from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

import pytest

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ,
    reason="No GITHUB_TOKEN environment variable set",
)
def test_multiple_sources(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "set.fd"])
    fd_version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "set.fd.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    skim_version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "set.skim.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    assert tuple(map(int, fd_version.split("."))) >= (4, 4, 3)
    assert tuple(map(int, skim_version.split("."))) == (0, 0, 0)
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(commit)
    assert fd_version in commit
    assert "sharkdp/fd/compare/v0.0.0..." in commit
    assert "skim" not in commit


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ,
    reason="No GITHUB_TOKEN environment variable set",
)
def test_let_bound_version(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "let-bound-version"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "let-bound-version.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    assert tuple(map(int, version.split("."))) >= (8, 5, 2)
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(commit)
    assert version in commit
    assert "github" in commit
    assert "https://github.com/sharkdp/fd/compare/v8.0.0...v" in commit
