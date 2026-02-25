from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update.options import Options
from nix_update.update import update_package

if TYPE_CHECKING:
    from pathlib import Path


def test_update(testpkgs: Path) -> None:
    opts = Options(attribute="pnpm", import_path=str(testpkgs))
    update_package(opts)
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
