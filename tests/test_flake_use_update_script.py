from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


def test_update(testpkgs_git: Path) -> None:
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
    print(diff)
    assert "flake-use-update-script: 2025-08-23 ->" in diff
