#!/usr/bin/env python3

from nix_update.options import Options
from nix_update.update import update
import subprocess
import conftest


def test_update(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs() as path:
        opts = Options(attribute="pypi", import_path=str(path))
        update(opts)
        version = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--experimental-features",
                "nix-command",
                "-f",
                path,
                "pypi.version",
            ],
            text=True,
            stdout=subprocess.PIPE,
        )
        assert version.stdout.strip() >= "3.0.1"
