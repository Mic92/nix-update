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
def test_fixed_version_no_prefix(testpkgs_git: Path) -> None:
    main(
        [
            "--file",
            str(testpkgs_git),
            "--commit",
            "--version",
            "5.1.0",
            "fetchurl-github-release",
        ],
    )
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    assert "https://github.com/vrana/adminer/compare/v5.0.5...v5.1.0" in commit


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ,
    reason="No GITHUB_TOKEN environment variable set",
)
def test_fixed_version_yes_prefix(testpkgs_git: Path) -> None:
    main(
        [
            "--file",
            str(testpkgs_git),
            "--commit",
            "--version",
            "v5.1.0",
            "fetchurl-github-release",
        ],
    )
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    assert "https://github.com/vrana/adminer/compare/v5.0.5...v5.1.0" in commit


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ,
    reason="No GITHUB_TOKEN environment variable set",
)
def test_auto_version(testpkgs_git: Path) -> None:
    main(
        [
            "--file",
            str(testpkgs_git),
            "--commit",
            "fetchurl-github-release",
        ],
    )
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    assert "https://github.com/vrana/adminer/compare/v5.0.5...v" in commit
