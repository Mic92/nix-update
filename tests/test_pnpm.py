from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update.options import Options
from nix_update.update import update
from nix_update.version.version import VersionPreference

if TYPE_CHECKING:
    from pathlib import Path


def test_update(testpkgs: Path) -> None:
    # Pin to a version whose pnpm lockfile is compatible with the pnpm
    # fetcher in nixpkgs: flood >= 4.16 uses patchedDependencies, which
    # fails with ERR_PNPM_LOCKFILE_CONFIG_MISMATCH in fetchPnpmDeps.
    opts = Options(
        attribute="pnpm",
        import_path=str(testpkgs),
        version="4.15.0",
        version_preference=VersionPreference.FIXED,
    )
    update(opts)
    pnpm_hash = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs,
            "pnpm.pnpmDeps.outputHash",
        ],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    assert pnpm_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
