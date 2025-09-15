from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from tests import conftest


def test_simple(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
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
                path,
                "cargoLock.generate.simple.cargoDeps",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        diff = subprocess.run(
            ["git", "-C", path, "show"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(diff)
        assert (
            "https://github.com/jupyter-server/pycrdt/compare/v0.9.6...v0.9.8" in diff
        )


def test_with_lockfile_metadata_path(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
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
                path,
                "cargoLock.generate.with-lockfile-metadata-path.cargoDeps",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        diff = subprocess.run(
            ["git", "-C", path, "show"],
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
    helpers: conftest.Helpers,
) -> None:
    """A test for a project where the target Cargo.toml is outside a workspace.

    In this case, Cargo.lock is generated in the subdirectory where Cargo.toml is located, not in the project root.
    For example, https://github.com/lancedb/lance/blob/v0.16.1/Cargo.toml
    """
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
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
                path,
                "cargoLock.generate.with-lockfile-metadata-path-outside-workspace.cargoDeps",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        diff = subprocess.run(
            ["git", "-C", path, "show"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(diff)
        assert "https://github.com/lancedb/lance/compare/v0.15.0...v0.16.1" in diff
