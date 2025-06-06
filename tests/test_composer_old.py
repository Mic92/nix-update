import subprocess

from nix_update.options import Options
from nix_update.update import update
from nix_update.version.version import VersionPreference
from tests import conftest


def test_update(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs() as path:
        opts = Options(
            attribute="composer-old",
            import_path=str(path),
            # For 0.14.0 we get inconsistent lock file errors
            version="0.13.1",
            version_preference=VersionPreference.FIXED,
        )
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
                "composer-old.version",
            ],
            text=True,
            stdout=subprocess.PIPE,
            check=False,
        ).stdout.strip()
        assert tuple(map(int, version.split("."))) >= (0, 11, 1)
