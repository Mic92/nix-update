from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


def test_update_without_default_nix(testpkgs_git: Path) -> None:
    # Pure flake projects have no default.nix; the update script's nix-update
    # invocation must not fall back to it.
    subprocess.run(
        ["git", "-C", str(testpkgs_git), "rm", "-q", "default.nix"], check=True
    )
    subprocess.run(
        ["git", "-C", str(testpkgs_git), "commit", "-q", "-m", "drop default.nix"],
        check=True,
    )
    assert not (testpkgs_git / "default.nix").exists()

    main(
        [
            "--file",
            str(testpkgs_git),
            "--use-update-script",
            "--flake",
            "--commit",
            "flake-use-update-script",
        ],
    )

    diff = subprocess.run(
        ["git", "-C", str(testpkgs_git), "show"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    assert "flake-use-update-script: 2025-08-23 ->" in diff
