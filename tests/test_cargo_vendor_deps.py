from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


def test_rust_package(testpkgs_git: Path) -> None:
    main(
        [
            "--file",
            str(testpkgs_git),
            "--commit",
            "cargoVendorDeps.rustPackage",
            "--version",
            "0.7.3",
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
            "cargoVendorDeps.rustPackage.cargoDeps",
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
    assert "https://github.com/astral-sh/ruff/compare/0.7.0...0.7.3" in diff


def test_non_rust_package(testpkgs_git: Path) -> None:
    main(
        [
            "--file",
            str(testpkgs_git),
            "--commit",
            "cargoVendorDeps.nonRustPackage",
            "--version",
            "v1.3.3",
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
            "cargoVendorDeps.nonRustPackage.cargoDeps",
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
    assert "https://github.com/pop-os/popsicle/compare/1.3.0...1.3.3" in diff
