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
        attribute="custom-deps",
        import_path=str(testpkgs),
        version_preference=VersionPreference.SKIP,
        custom_deps=["yarnOfflineCacheCustom", "pnpmDepsCustom"],
    )
    update(opts)

    def get_attr(attr: str) -> str:
        return subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                testpkgs,
                attr,
            ],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()

    yarn_hash = get_attr("custom-deps.yarnOfflineCacheCustom.outputHash")
    assert yarn_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

    pnpm_hash = get_attr("custom-deps.pnpmDepsCustom.outputHash")
    assert pnpm_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
