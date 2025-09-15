from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from tests import conftest


def test_main(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(["--file", str(path), "--commit", "pypi"])
        version = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                path,
                "pypi.version",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        assert tuple(map(int, version.split("."))) >= (3, 0, 1)
        commit = subprocess.run(
            ["git", "-C", path, "log", "-1"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(commit)
        assert f"pypi: 2.0.0 -> {version}" in commit
        assert (
            f"https://github.com/Mic92/python-mpd2/blob/{version}/doc/changes.rst"
            in commit
        )
