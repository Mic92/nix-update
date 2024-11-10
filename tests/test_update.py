import os
import subprocess

import conftest
import pytest

from nix_update import main


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ, reason="No GITHUB_TOKEN environment variable set"
)
def test_multiple_sources(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(["--file", str(path), "--commit", "set.fd"])
        fd_version = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                path,
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
                path,
                "set.skim.version",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        assert tuple(map(int, fd_version.split("."))) >= (4, 4, 3)
        assert tuple(map(int, skim_version.split("."))) == (0, 0, 0)
        commit = subprocess.run(
            ["git", "-C", path, "log", "-1"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(commit)
        assert fd_version in commit
        assert "sharkdp/fd/compare/v0.0.0..." in commit
        assert "skim" not in commit


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ, reason="No GITHUB_TOKEN environment variable set"
)
def test_let_bound_version(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(["--file", str(path), "--commit", "let-bound-version"])
        version = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                path,
                "let-bound-version.version",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        assert tuple(map(int, version.split("."))) >= (8, 5, 2)
        commit = subprocess.run(
            ["git", "-C", path, "log", "-1"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(commit)
        assert version in commit
        assert "github" in commit
        assert "https://github.com/sharkdp/fd/compare/v8.0.0...v" in commit
