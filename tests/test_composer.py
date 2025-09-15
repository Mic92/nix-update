from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update.options import Options
from nix_update.update import update

if TYPE_CHECKING:
    from tests import conftest


def test_update(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs() as path:
        opts = Options(attribute="composer", import_path=str(path))
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
                "composer.version",
            ],
            text=True,
            stdout=subprocess.PIPE,
            check=False,
        ).stdout.strip()
        assert tuple(map(int, version.split("."))) >= (11, 3, 1)
