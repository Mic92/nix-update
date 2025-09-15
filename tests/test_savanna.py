from __future__ import annotations

import subprocess
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

import pytest

from nix_update.options import Options
from nix_update.update import update

if TYPE_CHECKING:
    from tests import conftest


def test_update(helpers: conftest.Helpers) -> None:
    try:
        response = urllib.request.urlopen(
            "https://download.savannah.nongnu.org/releases/xlog/?C=M&O=D",
            timeout=5,
        )
        response.read()
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        # savannah's api seems to have issues lately
        pytest.xfail("Savana is taking too long to respond")

    with helpers.testpkgs() as path:
        opts = Options(attribute="savanna", import_path=str(path))
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
                "savanna.version",
            ],
            text=True,
            stdout=subprocess.PIPE,
            check=False,
        ).stdout.strip()
        assert tuple(map(int, version.split("."))) >= (2, 0, 24)
