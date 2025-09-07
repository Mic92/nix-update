import subprocess

from nix_update import main
from tests import conftest


def test_update(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
                "--use-update-script",
                "--flake",
                "--commit",
                "flake-use-update-script",
            ],
        )

        diff = subprocess.run(
            ["git", "-C", path, "show"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        print(diff)
        assert "flake-use-update-script: 2025-08-23 ->" in diff
