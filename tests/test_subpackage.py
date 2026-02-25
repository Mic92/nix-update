from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update.options import Options
from nix_update.update import update_package

if TYPE_CHECKING:
    from pathlib import Path


def test_update(testpkgs: Path) -> None:
    opts = Options(
        attribute="subpackage",
        subpackages=["autobrr-web"],
        import_path=str(testpkgs),
    )
    update_package(opts)

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

    subpackage_hash = get_attr("subpackage.autobrr-web.pnpmDeps.outputHash")
    assert subpackage_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

    src_hash = get_attr("subpackage.src.outputHash")
    assert src_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

    gomodules_hash = get_attr("subpackage.goModules.outputHash")
    assert gomodules_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

    version = get_attr("subpackage.version")
    assert tuple(map(int, version.split("."))) >= (1, 53, 0)
