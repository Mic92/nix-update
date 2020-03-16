import argparse
import tempfile

from .update import update
from .utils import run


def parse_args() -> argparse.Namespace:
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
    parser.add_argument("attribute", help="Attribute name within the file evaluated")
    parser.add_argument("version", nargs="?", help="Version to update to")
    return parser.parse_args()


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
    args = parse_args()
    update(args.file, args.attribute, args.version)
    if args.build:
        run(["nix", "build", "-f", args.file, args.attribute], stdout=None)
    if args.run:
        run(["nix", "run", "-f", args.file, args.attribute], stdout=None)

    if args.shell:
        nix_shell(args.file, args.attribute)


if __name__ == "__main__":
    main()
