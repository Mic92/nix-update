from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update.options import Options
from nix_update.update import update
from nix_update.version.version import VersionPreference

if TYPE_CHECKING:
    from pathlib import Path


def test_update(testpkgs: Path) -> None:
    opts = Options(
        attribute="composer-old",
        import_path=str(testpkgs),
        # For 0.14.0 we get inconsistent lock file errors
        version="0.13.1",
        version_preference=VersionPreference.FIXED,
    )
    update(opts)
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs,
            "composer-old.version",
        ],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    assert tuple(map(int, version.split("."))) >= (0, 11, 1)
