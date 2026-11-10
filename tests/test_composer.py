from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update.options import Options
from nix_update.update import update
from nix_update.version.version import VersionPreference

if TYPE_CHECKING:
    from pathlib import Path


def test_update(testpkgs: Path) -> None:
    # Pinned: upstream occasionally tags releases with a stale composer.lock,
    # which composerStrictValidation rejects.
    opts = Options(
        attribute="composer",
        version="11.3.1",
        version_preference=VersionPreference.FIXED,
        import_path=str(testpkgs),
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
            "composer.version",
        ],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    assert version == "11.3.1"
