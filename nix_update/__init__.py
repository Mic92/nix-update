import argparse
import os
import sys
import tempfile
from typing import NoReturn, Optional

from .eval import Package, eval_attr
from .options import Options
from .update import update
from .utils import run
from .version.version import VersionPreference


def die(msg: str) -> NoReturn:
    print(msg, file=sys.stderr)
    sys.exit(1)


def parse_args(args: list[str]) -> Options:
    parser = argparse.ArgumentParser()
    help = "File to import rather than default.nix. Examples, ./release.nix"
    parser.add_argument("-f", "--file", default="./.", help=help)
    parser.add_argument("--build", action="store_true", help="build the package")
    parser.add_argument(
        "--test", action="store_true", help="Run package's `passthru.tests`"
    )
    parser.add_argument(
        "--review", action="store_true", help="Run `nixpkgs-review wip`"
    )
    parser.add_argument("--format", action="store_true", help="Run `nixpkgs-fmt`")
    parser.add_argument(
        "--commit", action="store_true", help="Commit the updated package"
    )
    parser.add_argument(
        "--write-commit-message",
        metavar="FILE",
        help="Write commit message to FILE",
    )
    parser.add_argument(
        "-vr",
        "--version-regex",
        help="Regex to extract version with, i.e. 'jq-(.*)'",
        default="(.*)",
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
        "--version", nargs="?", help="Version to update to", default="stable"
    )
    parser.add_argument(
        "--override-filename",
        nargs="?",
        help="Set filename where nix-update will update version/hash",
        default=None,
    )
    parser.add_argument("attribute", help="Attribute name within the file evaluated")
    a = parser.parse_args(args)
    return Options(
        import_path=a.file,
        build=a.build,
        commit=a.commit,
        write_commit_message=a.write_commit_message,
        run=a.run,
        shell=a.shell,
        version=a.version,
        version_preference=VersionPreference.from_str(a.version),
        attribute=a.attribute,
        test=a.test,
        version_regex=a.version_regex,
        review=a.review,
        format=a.format,
        override_filename=a.override_filename,
    )


def nix_shell(options: Options) -> None:
    import_path = os.path.realpath(options.import_path)
    expr = f"with import {import_path} {{}}; mkShell {{ buildInputs = [ {options.attribute} ]; }}"
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "default.nix")
        with open(path, "w") as f:
            f.write(expr)
        run(["nix-shell", path], stdout=None, check=False)


def git_has_diff(git_dir: str, package: Package) -> bool:
    diff = run(["git", "-C", git_dir, "diff", "--", package.filename])
    return len(diff.stdout) > 0


def format_commit_message(package: Package) -> str:
    new_version = getattr(package.new_version, "number", None)
    if (
        new_version
        and package.old_version != new_version
        and new_version.startswith("v")
    ):
        new_version = new_version[1:]
    msg = f"{package.attribute}: {package.old_version} -> {new_version}"
    if package.changelog:
        msg += f"\n\nChangelog: {package.changelog}"
    return msg


def git_commit(git_dir: str, package: Package) -> None:
    msg = format_commit_message(package)
    new_version = package.new_version
    run(["git", "-C", git_dir, "add", package.filename], stdout=None)
    if new_version and package.old_version != new_version.number:
        run(
            ["git", "-C", git_dir, "commit", "--verbose", "--message", msg], stdout=None
        )
    else:
        with tempfile.NamedTemporaryFile(mode="w") as f:
            f.write(msg)
            f.flush()
            run(
                ["git", "-C", git_dir, "commit", "--verbose", "--template", f.name],
                stdout=None,
            )


def write_commit_message(path: str, package: Package) -> None:
    with open(path, "w") as f:
        f.write(format_commit_message(package))
        f.write("\n")


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
        git_dir = find_git_root(os.path.dirname(import_path))

    if git_dir is None:
        die(f"Could not find a git repository relative to {import_path}")

    output = run(["git", "-C", git_dir, "diff", "--staged"])
    if output.stdout != "":
        die(
            f"Please remove staged files before running {sys.argv[0]} with the commit flag"
        )
    return git_dir


def nix_run(options: Options) -> None:
    cmd = ["nix", "shell", "--extra-experimental-features", "nix-command"]
    run(
        cmd + ["-f", options.import_path, options.attribute],
        stdout=None,
        check=False,
    )


def nix_build(options: Options) -> None:
    cmd = [
        "nix",
        "build",
        "--extra-experimental-features",
        "nix-command",
        "-L",
        "-f",
        options.import_path,
        options.attribute,
    ]
    run(cmd, stdout=None)


def nix_test(package: Package) -> None:
    if not package.tests:
        die(f"Package '{package.name}' does not define any tests")

    tests = []
    for t in package.tests:
        tests.append("-A")
        tests.append(f"{package.attribute}.tests.{t}")
    cmd = ["nix-build"] + tests
    run(cmd, stdout=None)


def nixpkgs_review() -> None:
    cmd = [
        "nixpkgs-review",
        "wip",
    ]
    run(cmd, stdout=None)


def nixpkgs_fmt(package: Package, git_dir: Optional[str]) -> None:
    cmd = ["nixpkgs-fmt", package.filename]
    run(cmd, stdout=None)
    if git_dir is not None:
        run(["git", "-C", git_dir, "add", package.filename], stdout=None)


def main(args: list[str] = sys.argv[1:]) -> None:
    options = parse_args(args)
    if not os.path.exists(options.import_path):
        die(f"path {options.import_path} does not exist")

    git_dir = None
    if options.commit or options.review:
        git_dir = validate_git_dir(options.import_path)

    package = update(options)

    if options.build:
        nix_build(options)

    if options.run:
        nix_run(options)

    if options.shell:
        nix_shell(options)

    if not git_dir:
        git_dir = find_git_root(options.import_path)

    changes_detected = not git_dir or git_has_diff(git_dir, package)

    if not changes_detected:
        print("No changes detected, skipping remaining steps")
        return

    if options.test:
        nix_test(package)

    if options.review:
        nixpkgs_review()

    if options.format:
        nixpkgs_fmt(package, git_dir)

    if options.commit:
        assert git_dir is not None
        if package.changelog:
            # If we have a changelog we will re-eval the package in case it has changed
            package.changelog = eval_attr(options).changelog
        git_commit(git_dir, package)

    if options.write_commit_message is not None:
        write_commit_message(options.write_commit_message, package)


if __name__ == "__main__":
    main()
