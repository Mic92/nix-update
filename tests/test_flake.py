import subprocess

from nix_update import main
from tests import conftest


def test_main(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(["--file", str(path), "--flake", "--commit", "--test", "crate"])
        version = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "flakes nix-command",
                f"{path}#crate.version",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        assert tuple(map(int, version.split("."))) >= (8, 5, 2)
        commit = subprocess.run(
            ["git", "-C", path, "log", "-1"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(commit)
        assert f"crate: 8.0.0 -> {version}" in commit
        assert "https://diff.rs/fd-find/8.0.0/" in commit

        diff = subprocess.run(
            ["git", "-C", path, "show"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(diff)
        assert "https://diff.rs/fd-find/8.0.0/10.2.0" in diff


def test_update_script(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
                "--flake",
                "--commit",
                "--test",
                "--use-update-script",
                "crate",
            ],
        )
        version = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "flakes nix-command",
                f"{path}#crate.version",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        assert tuple(map(int, version.split("."))) >= (8, 5, 2)
        commit = subprocess.run(
            ["git", "-C", path, "log", "-1"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(commit)
        assert f"crate: 8.0.0 -> {version}" in commit
