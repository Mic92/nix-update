from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

from nix_update import main
from nix_update.version.github import fetch_github_commit
from nix_update.version.version import Version

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


def test_fetch_github_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    tag_name = "v9.0.0"
    tag_sha = "abc123"
    tag_object_url = "https://api.github.com/repos/sharkdp/fd/git/tags/abc123"
    commit_sha = "def456def456def456def456def456def456def456"
    commit_date_str = "2023-01-15T12:00:00+00:00"
    commit_date = datetime(2023, 1, 15, 12, 0, 0, tzinfo=UTC)

    url = urlparse(f"https://github.com/sharkdp/fd/archive/{tag_name}.tar.gz")
    version = Version(number=tag_name)

    tag_ref_response = json.dumps(
        {
            "object": {
                "url": tag_object_url,
                "sha": tag_sha,
            },
        },
    ).encode()

    tag_object_response = json.dumps(
        {
            "object": {
                "sha": commit_sha,
            },
        },
    ).encode()

    commit_response = json.dumps(
        {
            "commit": {
                "committer": {
                    "date": commit_date_str,
                },
            },
        },
    ).encode()

    responses = iter([tag_ref_response, tag_object_response, commit_response])

    def mock_dorequest(
        url: object,  # noqa: ARG001
        feed_url: str,  # noqa: ARG001
        extra_headers: object = None,  # noqa: ARG001
    ) -> bytes:
        return next(responses)

    monkeypatch.setattr("nix_update.version.github._dorequest", mock_dorequest)

    commit = fetch_github_commit(url, version)

    assert commit is not None
    assert commit.sha == commit_sha
    assert commit.date == commit_date


def test_fetch_github_commit_unmatched_url() -> None:
    url = urlparse("https://example.com/some/path")
    version = Version(number="v1.0.0")

    result = fetch_github_commit(url, version)

    assert result is None


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
