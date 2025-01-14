import subprocess

import conftest

from nix_update.options import Options
from nix_update.update import update


def test_update(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs() as path:
        opts = Options(attribute="npm", import_path=str(path))
        update(opts)
        version = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                path,
                "npm.version",
            ],
            text=True,
            stdout=subprocess.PIPE,
            check=False,
        ).stdout.strip()
        assert tuple(map(int, version.split("."))) > (10, 8, 6)
