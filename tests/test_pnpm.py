import subprocess

import conftest

from nix_update.options import Options
from nix_update.update import update


def test_update(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs() as path:
        opts = Options(attribute="pnpm", import_path=str(path))
        update(opts)
        pnpm_hash = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                path,
                "pnpm.pnpmDeps.outputHash",
            ],
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        assert pnpm_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
