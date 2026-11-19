from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import dependency_hashes
from nix_update.options import Options
from nix_update.update import update

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_update(testpkgs: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prefetched: list[str] = []
    nix_prefetch = dependency_hashes.nix_prefetch

    def recording_nix_prefetch(opts: Options, attr: str | None) -> str:
        prefetched.append(f"{opts.attribute}.{attr}")
        return nix_prefetch(opts, attr)

    monkeypatch.setattr(dependency_hashes, "nix_prefetch", recording_nix_prefetch)

    opts = Options(
        attribute="subpackage",
        subpackages=["autobrr-web"],
        import_path=str(testpkgs),
    )
    update(opts)

    assert "subpackage.autobrr-web.src" not in prefetched

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
