import subprocess

from nix_update.options import Options
from nix_update.update import update
from tests import conftest


def test_update(helpers: conftest.Helpers) -> None:
    with helpers.testpkgs() as path:
        opts = Options(
            attribute="subpackage",
            subpackages=["autobrr-web"],
            import_path=str(path),
        )
        update(opts)

        def get_attr(attr: str) -> str:
            return subprocess.run(
                [
                    "nix",
                    "eval",
                    "--raw",
                    "--extra-experimental-features",
                    "nix-command",
                    "-f",
                    path,
                    attr,
                ],
                text=True,
                stdout=subprocess.PIPE,
                check=False,
            ).stdout.strip()

        subpackage_hash = get_attr("subpackage.autobrr-web.pnpmDeps.outputHash")
        assert subpackage_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

        src_hash = get_attr("subpackage.src.outputHash")
        assert src_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

        gomodules_hash = get_attr("subpackage.goModules.outputHash")
        assert gomodules_hash != "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

        version = get_attr("subpackage.version")
        assert tuple(map(int, version.split("."))) >= (1, 53, 0)
