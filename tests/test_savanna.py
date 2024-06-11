import subprocess
import urllib.error
import urllib.request

import conftest
import pytest

from nix_update.options import Options
from nix_update.update import update


def test_update(helpers: conftest.Helpers) -> None:
    try:
        response = urllib.request.urlopen(
            "https://download.savannah.nongnu.org/releases/fileschanged/?C=M&O=D",
            timeout=5,
        )
        response.read()
    except Exception:
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
        ).stdout.strip()
        assert tuple(map(int, version.split("."))) >= (0, 6, 8)
