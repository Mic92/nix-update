from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


def test_simple(testpkgs_git: Path) -> None:
    main(
        [
            "--file",
            str(testpkgs_git),
            "--commit",
            "cargoLock.generate.simple",
            "--version",
            "v0.9.8",
            "--generate-lockfile",
        ],
    )
    subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "cargoLock.generate.simple.cargoDeps",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    diff = subprocess.run(
        ["git", "-C", str(testpkgs_git), "show"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(diff)
    assert "https://github.com/jupyter-server/pycrdt/compare/v0.9.6...v0.9.8" in diff


def test_with_lockfile_metadata_path(testpkgs_git: Path) -> None:
    main(
        [
            "--file",
            str(testpkgs_git),
            "--commit",
            "cargoLock.generate.with-lockfile-metadata-path",
            "--version",
            "0.12.0",
            "--generate-lockfile",
            "--lockfile-metadata-path",
            "python",
        ],
    )
    subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            str(testpkgs_git),
            "cargoLock.generate.with-lockfile-metadata-path.cargoDeps",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    diff = subprocess.run(
        ["git", "-C", str(testpkgs_git), "show"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(diff)
    assert (
        "https://github.com/lancedb/lancedb/compare/python-v0.11.0...python-v0.12.0"
        in diff
    )


def test_with_lockfile_metadata_path_outside_workspace(
    testpkgs_git: Path,
) -> None:
    """A test for a project where the target Cargo.toml is outside a workspace.

    In this case, Cargo.lock is generated in the subdirectory where Cargo.toml is located, not in the project root.
    For example, https://github.com/lancedb/lance/blob/v0.16.1/Cargo.toml
    """
    main(
        [
            "--file",
            str(testpkgs_git),
            "--commit",
            "cargoLock.generate.with-lockfile-metadata-path-outside-workspace",
            "--version",
            "v0.16.1",
            "--generate-lockfile",
            "--lockfile-metadata-path",
            "python",
        ],
    )
    subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            str(testpkgs_git),
            "cargoLock.generate.with-lockfile-metadata-path-outside-workspace.cargoDeps",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    diff = subprocess.run(
        ["git", "-C", str(testpkgs_git), "show"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(diff)
    assert "https://github.com/lancedb/lance/compare/v0.15.0...v0.16.1" in diff
