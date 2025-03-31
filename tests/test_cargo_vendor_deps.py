import subprocess

import conftest

from nix_update import main


def test_rust_package(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
                "--commit",
                "cargoVendorDeps.rustPackage",
                "--version",
                "0.7.3",
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
                "cargoVendorDeps.rustPackage.cargoDeps",
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
        assert "https://github.com/astral-sh/ruff/compare/0.7.0...0.7.3" in diff


def test_non_rust_package(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
                "--commit",
                "cargoVendorDeps.nonRustPackage",
                "--version",
                "v1.3.3",
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
                "cargoVendorDeps.nonRustPackage.cargoDeps",
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
        assert "https://github.com/pop-os/popsicle/compare/1.3.0...1.3.3" in diff
