from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


def test_main(testpkgs_git: Path) -> None:
    main(
        [
            "--file",
            str(testpkgs_git),
            "--commit",
            "net-news-wire",
            "--version-regex",
            "^mac-(\\d+\\.\\d+\\.\\d+(?:b\\d+)?)$",
        ],
    )
    version = get_nix_value(testpkgs_git, "net-news-wire.version")
    src = get_nix_value(testpkgs_git, "net-news-wire.src")
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "show"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(commit)
    assert src != "/nix/store/8k7nkbk4xbxwc6zc2bp85i8pvbvzzx6a-NetNewsWire6.1.5.zip"
    assert version != "6.1.5"
    assert version in commit
    assert "net-news-wire: 6.1.5 ->" in commit


def test_groups(testpkgs_git: Path) -> None:
    # Get the initial version
    initial_version = get_nix_value(testpkgs_git, "postgresql.version")

    main(
        [
            "--file",
            str(testpkgs_git),
            "postgresql",
            "--version-regex",
            "^REL_(\\d+)_(\\d+)(?:_(\\d+))?$",
        ],
    )
    version = get_nix_value(testpkgs_git, "postgresql.version")
    print(version)

    # The version should have been updated from initial
    assert version != initial_version

    # PostgreSQL versions should be in major.minor format (e.g., 17.6, 18.0)
    assert "." in version

    # Check that it's a valid PostgreSQL version format
    parts = version.split(".")
    min_version_parts = 2  # PostgreSQL uses major.minor(.patch) format
    assert len(parts) >= min_version_parts
    assert all(part.isdigit() for part in parts)


def get_nix_value(path: Path, key: str) -> str:
    return subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            path,
            key,
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
