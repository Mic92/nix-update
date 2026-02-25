from __future__ import annotations

import subprocess
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

import pytest

from nix_update.options import Options
from nix_update.update import update_package

if TYPE_CHECKING:
    from pathlib import Path


def test_update(testpkgs: Path) -> None:
    try:
        response = urllib.request.urlopen(
            "https://download.savannah.nongnu.org/releases/xlog/?C=M&O=D",
            timeout=5,
        )
        response.read()
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        # savannah's api seems to have issues lately
        pytest.xfail("Savana is taking too long to respond")

    opts = Options(attribute="savanna", import_path=str(testpkgs))
    update_package(opts)
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs,
            "savanna.version",
        ],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    assert tuple(map(int, version.split("."))) >= (2, 0, 24)
