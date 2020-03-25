import argparse
import tempfile
import os
import sys
from typing import Optional, NoReturn

from .update import update
from .utils import run
from .options import Options
from .eval import Package


def die(msg: str) -> NoReturn:
    print(msg, file=sys.stderr)
    sys.exit(1)


def parse_args() -> Options:
    parser = argparse.ArgumentParser()
    help = "File to import rather than default.nix. Examples, ./release.nix"
    parser.add_argument("-f", "--file", default="./.", help=help)
    parser.add_argument("--build", action="store_true", help="build the package")
    parser.add_argument(
        "--commit", action="store_true", help="Commit the updated package"
    )
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
        commit=args.commit,
        run=args.run,
        shell=args.shell,
        version=args.version,
        attribute=args.attribute,
    )


def nix_shell(options: Options) -> None:
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write(
            f"""
        with import {options.import_path}; mkShell {{ buildInputs = [ {options.attribute} ]; }}
        """
        )
        f.flush()
        run(["nix-shell", f.name], stdout=None, check=False)


def git_commit(git_dir: str, attribute: str, package: Package) -> None:

    run(["git", "-C", git_dir, "add", package.filename], stdout=None)
    diff = run(["git", "-C", git_dir, "diff", "--staged"])
    if len(diff.stdout) == 0:
        print("No changes made, skip commit", file=sys.stderr)
        return

    new_version = package.new_version
    if new_version and package.old_version != new_version:
        if new_version.startswith("v"):
            new_version = new_version[1:]
        msg = f"{attribute}: {package.old_version} -> {new_version}"
        run(
            ["git", "-C", git_dir, "commit", "--verbose", "--message", msg], stdout=None
        )
    else:
        with tempfile.NamedTemporaryFile(mode="w") as f:
            f.write(f"{attribute}:")
            f.flush()
            run(
                ["git", "-C", git_dir, "commit", "--verbose", "--template", f.name],
                stdout=None,
            )


def find_git_root(path: str) -> Optional[str]:
    prefix = [path]
    release_nix = [".git"]
    while True:
        root_path = os.path.join(*prefix)
        release_nix_path = os.path.join(root_path, *release_nix)
        if os.path.exists(release_nix_path):
            return root_path
        if os.path.abspath(root_path) == "/":
            return None
        prefix.append("..")


def validate_git_dir(import_path: str) -> str:
    if os.path.isdir(import_path):
        git_dir = find_git_root(import_path)
    else:
        git_dir = find_git_root(os.path.basename(import_path))

    if git_dir is None:
        die(f"Could not find a git repository relative to {import_path}")

    output = run(["git", "-C", git_dir, "diff", "--staged"])
    if output.stdout != "":
        die(
            f"Please remove staged files before running {sys.argv[0]} with the commit flag"
        )
    return git_dir


def nix_run(options: Options) -> None:
    run(
        ["nix", "run", "-f", options.import_path, options.attribute],
        stdout=None,
        check=False,
    )


def nix_build(options: Options) -> None:
    run(
        ["nix", "build", "-f", options.import_path, options.attribute],
        stdout=None,
        check=False,
    )


def main() -> None:
    options = parse_args()

    if not os.path.exists(options.import_path):
        die(f"path {options.import_path} does not exists")

    if options.commit:
        git_dir = validate_git_dir(options.import_path)

    package = update(options)

    if options.build:
        nix_build(options)

    if options.run:
        nix_run(options)

    if options.shell:
        nix_shell(options)

    if options.commit:
        git_commit(git_dir, options.attribute, package)


if __name__ == "__main__":
    main()
