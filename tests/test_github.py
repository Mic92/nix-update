import subprocess

import conftest

from nix_update import main


def test_main(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(["--file", str(path), "--commit", "github"])
        version = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                path,
                "github.version",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        assert version >= "8.5.2"
        commit = subprocess.run(
            ["git", "-C", path, "log", "-1"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(commit)
        assert version in commit
        assert "github" in commit
        assert "https://github.com/sharkdp/fd/compare/v8.0.0...v" in commit
