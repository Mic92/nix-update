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
            "--commit",
            "non-flake-update-script",
        ],
    )

    diff = subprocess.run(
        ["git", "-C", str(testpkgs_git), "show"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(diff)
    assert "non-flake-update-script: 1.0.0 -> 1.2.3" in diff
    assert '+  version = "1.2.3";' in diff
