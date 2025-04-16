import argparse
import os
import shlex
import shutil
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

from .eval import CargoLockInSource, Package, eval_attr
from .options import Options
from .update import update
from .utils import run
from .version.version import VersionPreference


def die(msg: str) -> NoReturn:
    print(msg, file=sys.stderr)
    sys.exit(1)


def parse_args(args: list[str]) -> Options:
    parser = argparse.ArgumentParser()
    help_msg = "File to import rather than default.nix. Examples, ./release.nix"
    parser.add_argument("-f", "--file", default="./.", help=help_msg)
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Hide informational messages"
    )
    parser.add_argument(
        "-F", "--flake", action="store_true", help="Update a flake attribute instead"
    )
    parser.add_argument("--build", action="store_true", help="build the package")
    parser.add_argument(
        "--test", action="store_true", help="Run package's `passthru.tests`"
    )
    parser.add_argument(
        "--review", action="store_true", help="Run `nixpkgs-review wip`"
    )
    parser.add_argument("--format", action="store_true", help="Run `nixfmt`")
    parser.add_argument(
        "--commit", action="store_true", help="Commit the updated package"
    )
    parser.add_argument(
        "-u",
        "--use-update-script",
        action="store_true",
        help="Use passthru.updateScript instead if possible",
    )
    parser.add_argument(
        "--update-script-args",
        default=[],
        type=shlex.split,
        help="Args to pass to `nix-shell maintainers/scripts/update.nix`, subject to splitting.",
    )
    parser.add_argument(
        "--url",
        help="URL to the repository to check for a release instead of using the URL in the src attribute of the package",
    )
    parser.add_argument(
        "--print-commit-message",
        action="store_true",
        help="Print commit message to stdout (implies --quiet)",
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
        "--version",
        nargs="?",
        default=VersionPreference.STABLE,
        help="Version to update to. Possible values are: "
        + ", ".join(VersionPreference),
    )
    parser.add_argument(
        "--override-filename",
        nargs="?",
        help="Set filename where nix-update will update version/hash",
        default=None,
    )
    parser.add_argument(
        "--system",
        help="The system used to to calculate the hash and run other nix commands",
        default=None,
    )

    default_attribute = os.getenv("UPDATE_NIX_ATTR_PATH")
    parser.add_argument(
        "attribute",
        default=default_attribute,
        nargs="?" if default_attribute else None,  # type: ignore[arg-type]
        help="""Attribute name within the file evaluated (defaults to environment variable "UPDATE_NIX_ATTR_PATH")""",
    )
    parser.add_argument(
        "--generate-lockfile",
        action="store_true",
        help="Generate lockfile and replace vendored one",
    )
    parser.add_argument(
        "--lockfile-metadata-path",
        help="Path to the directory containing the metadata (e.g. Cargo.toml) referenced by the lockfile",
        default=".",
    )
    parser.add_argument(
        "-s",
        "--subpackage",
        action="append",
        help="Attribute of a subpackage that nix-update should try to update hashes for",
        default=None,
    )
    parser.add_argument(
        "--src-only",
        help="Only update the source, not dependencies such as npmDeps, cargoDeps or nugetDeps",
        action="store_true",
    )
    parser.add_argument(
        "--option",
        help="Nix option to set",
        action="append",
        nargs=2,
        metavar=("name", "value"),
        default=[],
    )

    a = parser.parse_args(args)
    extra_flags = ["--extra-experimental-features", "flakes nix-command"]
    if a.system:
        extra_flags.extend(["--system", a.system])
    for name, value in a.option:
        extra_flags.extend(["--option", name, value])

    return Options(
        import_path=os.path.realpath(a.file),
        quiet=a.quiet or a.print_commit_message,
        flake=a.flake,
        build=a.build,
        commit=a.commit,
        use_update_script=a.use_update_script,
        update_script_args=a.update_script_args,
        subpackages=a.subpackage,
        url=a.url,
        print_commit_message=a.print_commit_message,
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
        system=a.system,
        generate_lockfile=a.generate_lockfile,
        lockfile_metadata_path=a.lockfile_metadata_path,
        src_only=a.src_only,
        extra_flags=extra_flags,
    )


def nix_shell(options: Options) -> None:
    if options.flake:
        run(
            [
                "nix",
                "shell",
                f"{options.import_path}#{options.attribute}",
                *options.extra_flags,
            ],
            stdout=None,
            check=False,
            quiet=options.quiet,
        )
    else:
        expr = f"let pkgs = import {options.escaped_import_path} {{}}; in pkgs.mkShell {{ buildInputs = [ pkgs.{options.escaped_attribute} ]; }}"
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "default.nix"
            path.write_text(expr)
            run(
                ["nix-shell", str(path), *options.extra_flags],
                stdout=None,
                check=False,
                quiet=options.quiet,
            )


def git_has_diff(git_dir: str, package: Package, quiet: bool) -> bool:
    diff = run(["git", "-C", git_dir, "diff", "--", package.filename], quiet=quiet)
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
    if package.diff_url:
        msg += f"\n\nDiff: {package.diff_url}"
    if package.changelog:
        msg += f"\n\nChangelog: {package.changelog}"
    return msg


def git_commit(git_dir: str, package: Package, quiet: bool) -> None:
    msg = format_commit_message(package)
    new_version = package.new_version
    files_changed = [package.filename]
    if isinstance(package.cargo_lock, CargoLockInSource):
        files_changed.append(package.cargo_lock.path)
    if new_version and (
        package.old_version != new_version.number
        or (new_version.rev and new_version.rev != package.rev)
    ):
        run(
            [
                "git",
                "-C",
                git_dir,
                "commit",
                "--verbose",
                "--message",
                msg,
                *files_changed,
            ],
            stdout=None,
            quiet=quiet,
        )
    else:
        with tempfile.NamedTemporaryFile(mode="w") as f:
            f.write(msg)
            f.flush()
            run(
                [
                    "git",
                    "-C",
                    git_dir,
                    "commit",
                    "--verbose",
                    "--template",
                    f.name,
                    *files_changed,
                ],
                stdout=None,
                quiet=quiet,
            )


def print_commit_message(package: Package) -> None:
    print(format_commit_message(package))
    print("\n")


def write_commit_message(path: str, package: Package) -> None:
    with open(path, "w") as f:
        f.write(format_commit_message(package))
        f.write("\n")


def find_git_root(path: str) -> str | None:
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

    return git_dir


def nix_run(options: Options) -> None:
    cmd = ["nix", "shell", "-L", *options.extra_flags]

    if options.flake:
        cmd.append(f"{options.import_path}#{options.attribute}")
    else:
        cmd.extend(["-f", options.import_path, options.attribute])
    run(
        cmd,
        stdout=None,
        check=False,
        quiet=options.quiet,
    )


def nix_build_tool() -> str:
    "Return `nom` if found in $PATH"
    if shutil.which("nom"):
        return "nom"
    return "nix"


def nix_build(options: Options) -> None:
    cmd = [nix_build_tool(), "build", "-L", *options.extra_flags]
    if options.flake:
        cmd.append(f"{options.import_path}#{options.attribute}")
    else:
        cmd.extend(["-f", options.import_path, options.attribute])
    run(cmd, stdout=None, quiet=options.quiet)


def nix_test(opts: Options, package: Package) -> None:
    if not package.tests:
        die(f"Package '{package.name}' does not define any tests")

    cmd = [nix_build_tool(), "build", "-L", *opts.extra_flags]

    if opts.flake:
        for t in package.tests:
            cmd.append(f"{opts.import_path}#{package.attribute}.tests.{t}")
    else:
        cmd.extend(["-f", opts.import_path])
        for t in package.tests:
            cmd.append("-A")
            cmd.append(f"{package.attribute}.tests.{t}")
    run(cmd, stdout=None)


def nixpkgs_review() -> None:
    cmd = [
        "nixpkgs-review",
        "wip",
    ]
    run(cmd, stdout=None)


def main(args: list[str] = sys.argv[1:]) -> None:
    options = parse_args(args)
    if not os.path.exists(options.import_path):
        die(f"path {options.import_path} does not exist")

    git_dir = None
    if options.commit or options.review:
        git_dir = validate_git_dir(options.import_path)

    package = update(options)

    if package.maintainers:
        print("Package maintainers:")
        for maintainer in package.maintainers:
            print(
                f"  - {maintainer['name']}"
                + (f" (@{maintainer['github']})" if "github" in maintainer else "")
            )

    if options.build:
        nix_build(options)

    if options.run:
        nix_run(options)

    if options.shell:
        nix_shell(options)

    if not git_dir:
        git_dir = find_git_root(options.import_path)

    changes_detected = not git_dir or git_has_diff(git_dir, package, options.quiet)

    if not changes_detected:
        if not options.quiet:
            print("No changes detected, skipping remaining steps")
        return

    if options.test:
        nix_test(options, package)

    if options.review:
        if options.flake:
            print("--review is unsupported with --flake")
        else:
            nixpkgs_review()

    if options.format:
        run(["nixfmt", package.filename], stdout=None, quiet=options.quiet)

    if options.commit:
        assert git_dir is not None
        if package.changelog:
            # If we have a changelog we will re-eval the package in case it has changed
            package.changelog = eval_attr(options).changelog
        git_commit(git_dir, package, quiet=options.quiet)

    if options.print_commit_message:
        print_commit_message(package)

    if options.write_commit_message is not None:
        write_commit_message(options.write_commit_message, package)


if __name__ == "__main__":
    main()
