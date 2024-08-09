import subprocess

import conftest

from nix_update import main


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
            ]
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
            ]
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
            "https://github.com/lancedb/lancedb/compare/python-v0.11.0...0.12.0" in diff
        )
