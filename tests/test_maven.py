from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update.options import Options
from nix_update.update import update_package

if TYPE_CHECKING:
    from pathlib import Path


def test_update(testpkgs: Path) -> None:
    opts = Options(attribute="maven", import_path=str(testpkgs))
    update_package(opts)
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs,
            "maven.version",
        ],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    assert tuple(map(int, version.split("."))) > (2, 7, 0)
