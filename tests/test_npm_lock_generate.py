import subprocess

from nix_update import main
from tests import conftest


def test_update(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs(init_git=True) as path:
        main(
            [
                "--file",
                str(path),
                "--commit",
                "npm-lock-generate",
                "--version",
                "v2.6.0",
                "--generate-lockfile",
            ],
        )
        npm_deps_name = subprocess.run(
            [
                "nix",
                "eval",
                "--raw",
                "--extra-experimental-features",
                "nix-command",
                "-f",
                path,
                "npm-lock-generate.npmDeps.name",
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
        assert "2.6.0" in npm_deps_name
        assert (
            "https://github.com/olrtg/emmet-language-server/compare/v2.5.0...v2.6.0"
            in diff
        )
