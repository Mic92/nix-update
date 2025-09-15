from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from tests import conftest


def test_update(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
                "--commit",
                "nuget-deps-generate",
                "--version",
                "v1.1.1",
                "--src-only",
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
                path,
                "nuget-deps-generate.nugetDeps",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        nuget_deps = json.loads(nuget_deps_raw)
        assert len(nuget_deps) == 0

        diff = subprocess.run(
            ["git", "-C", path, "log"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(diff)
        assert "https://github.com/ExOK/Celeste64/compare/v1.1.0...v1.1.1" in diff
