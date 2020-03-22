import argparse
import tempfile

from .update import update
from .utils import run
from .options import Options


def parse_args() -> Options:
    parser = argparse.ArgumentParser()
    help = "File to import rather than default.nix. Examples, ./release.nix"
    parser.add_argument("-f", "--file", default="./.", help=help)
    parser.add_argument("--build", action="store_true", help="build the package")
    parser.add_argument(
        "--run",
        action="store_true",
        help="provide a shell based on `nix run` with the package in $PATH",
    )
    parser.add_argument(
        "--shell", action="store_true", help="provide a shell with the package"
    )
    parser.add_argument(
        "--version", nargs="?", help="Version to update to", default="auto"
    )
    parser.add_argument("attribute", help="Attribute name within the file evaluated")
    args = parser.parse_args()
    return Options(
        import_path=args.file,
        build=args.build,
        run=args.run,
        shell=args.shell,
        version=args.version,
        attribute=args.attribute,
    )


def nix_shell(filename: str, attribute: str) -> None:
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write(
            f"""
        with import {filename}; mkShell {{ buildInputs = [ {attribute} ]; }}
        """
        )
        f.flush()
        run(["nix-shell", f.name], stdout=None)


def main() -> None:
    options = parse_args()
    update(options)
    if options.build:
        run(["nix", "build", "-f", options.file, options.attribute], stdout=None)
    if options.run:
        run(["nix", "run", "-f", options.file, options.attribute], stdout=None)

    if options.shell:
        nix_shell(options.file, options.attribute)


if __name__ == "__main__":
    main()
