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
            "--flake",
            "--commit",
            "--test",
            "--version",
            "10.2.0",
            "crate",
        ],
    )
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "flakes nix-command",
            f"{testpkgs_git}#crate.version",
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
    assert f"crate: 8.0.0 -> {version}" in commit
    assert "https://diff.rs/fd-find/8.0.0/" in commit

    diff = subprocess.run(
        ["git", "-C", str(testpkgs_git), "show"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(diff)
    assert f"https://diff.rs/fd-find/8.0.0/{version}" in diff


def test_update_script(testpkgs_git: Path) -> None:
    main(
        [
            "--file",
            str(testpkgs_git),
            "--flake",
            "--commit",
            "--test",
            "--use-update-script",
            "crate",
        ],
    )
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "flakes nix-command",
            f"{testpkgs_git}#crate.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    assert tuple(map(int, version.split("."))) >= (8, 5, 2)
    commit = subprocess.run(
        ["git", "-C", testpkgs_git, "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(commit)
    assert f"crate: 8.0.0 -> {version}" in commit
