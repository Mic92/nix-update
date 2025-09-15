from __future__ import annotations

import fileinput
import re
import subprocess
import sys
import tempfile
from functools import partial
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from .eval import Package
    from .options import Options

from .cargo import update_cargo_lock
from .errors import UpdateError
from .hashes import to_sri
from .lockfile import generate_lockfile
from .utils import run


def replace_hash(filename: str, current: str, target: str) -> None:
    normalized_hash = to_sri(target)
    if to_sri(current) != normalized_hash:
        with fileinput.FileInput(filename, inplace=True) as f:
            for original_line in f:
                modified_line = original_line.replace(current, normalized_hash)
                print(modified_line, end="")


def nix_prefetch(opts: Options, attr: str) -> str:
    expr = f"{opts.get_package()}.{attr}"

    extra_env: dict[str, str] = {}
    tempdir: tempfile.TemporaryDirectory[str] | None = None
    stderr = ""
    if extra_env.get("XDG_RUNTIME_DIR") is None:
        tempdir = tempfile.TemporaryDirectory()
        extra_env["XDG_RUNTIME_DIR"] = tempdir.name
    try:
        res = run(
            [
                "nix-build",
                "--expr",
                f'let src = {expr}; in (src.overrideAttrs or (f: src // f src)) (_: {{ outputHash = ""; outputHashAlgo = "sha256"; }})',
                *opts.extra_flags,
            ],
            extra_env=extra_env,
            stderr=subprocess.PIPE,
            check=False,
        )
        stderr = res.stderr.strip()
        # got:    xxx
        # expected 'xxx' but got 'xxx'
        regex = re.compile(r".*got(:|\s)\s*'?([^']*)('|$)")
        got = ""
        for line in reversed(stderr.split("\n")):
            if match := regex.fullmatch(line):
                got = match[2]
                break
    finally:
        if tempdir:
            tempdir.cleanup()

    if got == "":
        print(stderr, file=sys.stderr)
        msg = f"failed to retrieve hash when trying to update {opts.attribute}.{attr}"
        raise UpdateError(msg)
    return got


def update_hash_with_prefetch(
    attr_name: str,
    opts: Options,
    filename: str,
    current_hash: str,
) -> None:
    """Generic function to update a hash by prefetching with a specific attribute."""
    target_hash = nix_prefetch(opts, attr_name)
    replace_hash(filename, current_hash, target_hash)


# Create partial function for updating src hash (used elsewhere in the code)
update_src_hash = partial(update_hash_with_prefetch, "src")


def update_nuget_deps(opts: Options) -> None:
    """Update NuGet dependencies."""
    fetch_deps_script_path = run(
        [
            "nix-build",
            opts.import_path,
            "-A",
            f"{opts.attribute}.fetch-deps",
            "--no-out-link",
        ],
    ).stdout.strip()

    # Run the fetch-deps script without arguments - it determines the path itself
    run([fetch_deps_script_path])


def update_dependency_hashes(
    opts: Options,
    package: Package,
    *,
    update_hash: bool,
) -> None:
    if not (update_hash or not package.hash) or opts.src_only:
        return

    hash_updaters: dict[str, Callable[[Options, str, Any], None]] = {
        "go_modules": partial(update_hash_with_prefetch, "goModules"),
        "go_modules_old": partial(update_hash_with_prefetch, "go-modules"),
        "cargo_deps": partial(update_hash_with_prefetch, "cargoDeps"),
        "cargo_vendor_deps": partial(
            update_hash_with_prefetch,
            "cargoDeps.vendorStaging",
        ),
        "composer_deps": partial(update_hash_with_prefetch, "composerVendor"),
        "composer_deps_old": partial(update_hash_with_prefetch, "composerRepository"),
        "npm_deps": (lambda o, f, _d: generate_lockfile(o, f, "npm", o.get_package()))
        if opts.generate_lockfile
        else partial(update_hash_with_prefetch, "npmDeps"),
        "pnpm_deps": partial(update_hash_with_prefetch, "pnpmDeps"),
        "yarn_deps": partial(update_hash_with_prefetch, "yarnOfflineCache"),
        "yarn_deps_old": partial(update_hash_with_prefetch, "offlineCache"),
        "maven_deps": partial(update_hash_with_prefetch, "fetchedMavenDeps"),
        "mix_deps": partial(update_hash_with_prefetch, "mixFodDeps"),
        "zig_deps": partial(update_hash_with_prefetch, "zigDeps"),
        "cargo_lock": update_cargo_lock,
    }

    # Update all dependency hashes using registry
    for attr_name, updater in hash_updaters.items():
        dep_value = getattr(package, attr_name, None)
        if dep_value:
            updater(opts, package.filename, dep_value)

    # Handle nuget deps separately since it's a boolean
    if package.has_nuget_deps:
        update_nuget_deps(opts)
