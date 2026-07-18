from __future__ import annotations

import json
import subprocess
from pathlib import Path

from nix_update.options import Options
from nix_update.update import update
from nix_update.version.version import VersionPreference


def test_update(testpkgs: Path) -> None:
    opts = Options(
        attribute="yarn-berry-missing-hashes",
        import_path=str(testpkgs),
        version_preference=VersionPreference.SKIP,
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

    yarn_hash = get_attr("yarn-berry-missing-hashes.yarnOfflineCache.outputHash")
    assert yarn_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

    missing_hashes = Path(get_attr("yarn-berry-missing-hashes.missingHashes"))
    data = json.loads(missing_hashes.read_text())

    assert isinstance(data, dict)
    assert len(data) > 0
