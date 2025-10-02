from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


def test_build_and_test_without_flake(testpkgs_git: Path) -> None:
    """Test that packages with multiple tests work correctly with --build and --test options without flakes."""
    # Run nix-update with both --build and --test options
    main(
        [
            "--file",
            str(testpkgs_git),
            "--commit",
            "--build",
            "--test",
            "--version",
            "3.1.1",
            "pypi",
        ],
    )

    # Verify the version was updated
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            str(testpkgs_git),
            "pypi.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    assert version == "3.1.1"
