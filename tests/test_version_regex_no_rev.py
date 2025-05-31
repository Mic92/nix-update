import subprocess
from pathlib import Path

from nix_update import main
from tests import conftest


def test_main(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
                "--commit",
                "net-news-wire",
                "--version-regex",
                "^mac-(\\d+\\.\\d+\\.\\d+(?:b\\d+)?)$",
            ],
        )
        version = get_nix_value(path, "net-news-wire.version")
        src = get_nix_value(path, "net-news-wire.src")
        commit = subprocess.run(
            ["git", "-C", path, "show"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(commit)
        assert src != "/nix/store/8k7nkbk4xbxwc6zc2bp85i8pvbvzzx6a-NetNewsWire6.1.5.zip"
        assert version != "6.1.5"
        assert version in commit
        assert "net-news-wire: 6.1.5 ->" in commit


def get_nix_value(path: Path, key: str) -> str:
    return subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            path,
            key,
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
