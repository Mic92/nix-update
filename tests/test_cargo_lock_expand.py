import subprocess

import conftest

from nix_update import main


def test_main(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            ["--file", str(path), "--commit", "cargoLock.expand", "--version", "v0.3.8"]
        )
        subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                path,
                "cargoLock.expand.cargoDeps",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        diff = subprocess.run(
            ["git", "-C", path, "show"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(diff)
        assert "cargoLock.expand: 0.3.7 -> 0.3.8"
        assert "Cargo.lock" in diff
        assert '+source = "git+' in diff
        assert "outputHashes" in diff
        assert "https://github.com/nix-community/nurl/compare/v0.3.7...v0.3.8" in diff
