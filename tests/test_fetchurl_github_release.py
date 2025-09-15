from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

import pytest

from nix_update import main

if TYPE_CHECKING:
    from tests import conftest


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ,
    reason="No GITHUB_TOKEN environment variable set",
)
def test_fixed_version_no_prefix(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
                "--commit",
                "--version",
                "5.1.0",
                "fetchurl-github-release",
            ],
        )
        commit = subprocess.run(
            ["git", "-C", path, "log", "-1"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        assert "https://github.com/vrana/adminer/compare/v5.0.5...v5.1.0" in commit


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ,
    reason="No GITHUB_TOKEN environment variable set",
)
def test_fixed_version_yes_prefix(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
                "--commit",
                "--version",
                "v5.1.0",
                "fetchurl-github-release",
            ],
        )
        commit = subprocess.run(
            ["git", "-C", path, "log", "-1"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        assert "https://github.com/vrana/adminer/compare/v5.0.5...v5.1.0" in commit


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ,
    reason="No GITHUB_TOKEN environment variable set",
)
def test_auto_version(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
                "--commit",
                "fetchurl-github-release",
            ],
        )
        commit = subprocess.run(
            ["git", "-C", path, "log", "-1"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        assert "https://github.com/vrana/adminer/compare/v5.0.5...v" in commit
