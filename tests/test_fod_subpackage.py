from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update.options import Options
from nix_update.update import update_package
from nix_update.version.version import VersionPreference

if TYPE_CHECKING:
    from pathlib import Path


def test_update(testpkgs: Path) -> None:
    opts = Options(
        attribute="fod-subpackage",
        subpackages=["node_modules"],
        import_path=str(testpkgs),
        version_preference=VersionPreference.SKIP,
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

    subpackage_hash = get_attr("fod-subpackage.node_modules.outputHash")
    assert subpackage_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

    src_hash = get_attr("fod-subpackage.src.outputHash")
    assert src_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
