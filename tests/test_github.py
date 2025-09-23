from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

import pytest

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def invalid_github_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixture that sets an invalid GitHub token for testing."""
    monkeypatch.setenv("GITHUB_TOKEN", "invalid_token")


def test_github_feed(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "github"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "github.version",
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


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ,
    reason="No GITHUB_TOKEN environment variable set",
)
def test_github_releases(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "github", "--use-github-releases"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "github.version",
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


@pytest.mark.skipif(
    "GITHUB_TOKEN" not in os.environ,
    reason="No GITHUB_TOKEN environment variable set",
)
def test_github_empty_fallback(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "github-no-release"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "github-no-release.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    assert tuple(map(int, version.split("."))) >= (4, 4, 3)
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(commit)
    assert version in commit
    assert "github" in commit
    assert (
        "https://github.com/ProtonVPN/proton-vpn-gtk-app/compare/v4.3.2...v" in commit
    )


@pytest.mark.usefixtures("invalid_github_token")
def test_github_tag(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "github-tag"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "github-tag.version",
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


@pytest.mark.usefixtures("invalid_github_token")
def test_github_feed_fallback(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "github"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "github.version",
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


@pytest.mark.usefixtures("invalid_github_token")
def test_github_fetchtree(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "github-fetchtree"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command fetch-tree",
            "-f",
            testpkgs_git,
            "github-fetchtree.version",
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


@pytest.mark.usefixtures("invalid_github_token")
def test_github_fetchtree_private(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "github-fetchtree-private"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command fetch-tree",
            "-f",
            testpkgs_git,
            "github-fetchtree-private.version",
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


def test_github_forcefetchgit(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "github-forcefetchgit"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "github-forcefetchgit.version",
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
