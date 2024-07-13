import subprocess

import conftest

from nix_update.options import Options
from nix_update.update import update


def test_update(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs() as path:
        opts = Options(attribute="mix", import_path=str(path))
        update(opts)
        mix_hash = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                path,
                "mix.mixFodDeps.outputHash",
            ],
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        assert mix_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
