import subprocess
from datetime import date
from urllib.parse import urlparse

import pytest

from nix_update.options import Options
from nix_update.update import update
from nix_update.version import VersionPreference, fetch_latest_version
from tests import conftest


def test_update(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs() as path:
        opts = Options(attribute="sourcehut", import_path=str(path))
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
                "sourcehut.version",
            ],
            text=True,
            stdout=subprocess.PIPE,
            check=False,
        ).stdout.strip()
        assert tuple(map(int, version.split("."))) >= (0, 3, 6)


@pytest.mark.usefixtures("helpers")
def test_branch() -> None:
    version = fetch_latest_version(
        urlparse("https://git.sr.ht/~jcc/addr-book-combine"),
        VersionPreference.BRANCH,
        "(.*)",
        "master",
    ).number
    version_date = date.fromisoformat(version[-10:])
    assert version_date >= date(2022, 12, 14)
