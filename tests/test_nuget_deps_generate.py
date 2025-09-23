from __future__ import annotations

import json
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
            "--commit",
            "nuget-deps-generate",
            "--version",
            "v1.1.1",
        ],
    )

    nuget_deps_raw = subprocess.run(
        [
            "nix",
            "eval",
            "--json",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "nuget-deps-generate.nugetDeps",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    nuget_deps = json.loads(nuget_deps_raw)
    assert len(nuget_deps) > 0

    diff = subprocess.run(
        ["git", "-C", str(testpkgs_git), "show"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(diff)
    assert "https://github.com/ExOK/Celeste64/compare/v1.1.0...v1.1.1" in diff
    assert "nuget-deps-generate/deps.json" in diff
