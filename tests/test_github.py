import os
import subprocess

import conftest
import pytest

from nix_update import main


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ, reason="No GITHUB_TOKEN environment variable set"
)
def test_github_api(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(["--file", str(path), "--commit", "github"])
        version = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                path,
                "github.version",
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


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ, reason="No GITHUB_TOKEN environment variable set"
)
def test_github_empty_fallback(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(["--file", str(path), "--commit", "github-no-release"])
        version = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                path,
                "github-no-release.version",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        assert tuple(map(int, version.split("."))) >= (4, 4, 3)
        commit = subprocess.run(
            ["git", "-C", path, "log", "-1"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(commit)
        assert version in commit
        assert "github" in commit
        assert (
            "https://github.com/ProtonVPN/proton-vpn-gtk-app/compare/v4.3.2...v"
            in commit
        )


def test_github_feed_fallback(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setenv("GITHUB_TOKEN", "invalid_token")
        main(["--file", str(path), "--commit", "github"])
        version = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                path,
                "github.version",
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
