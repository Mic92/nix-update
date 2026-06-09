from __future__ import annotations

import fileinput
import re
import subprocess
import tempfile
from functools import partial
from pathlib import Path
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


def extract_hash_from_nix_error(stderr: str) -> str | None:
    """Extract hash from Nix build error output.

    Handles various formats:
    - got:    xxx
    - got:    sha256:xxxxx
    - got:    sha256-xxxxx=
    - got:    blake3-xxxxx=
    - expected 'xxx' but got 'xxx'

    Returns the hash string or None if not found.
    """
    # Regex handles both hex hashes and SRI hashes (e.g., sha256-base64=, blake3-base64=)
    regex = re.compile(
        r".*got(:|\s)\s*'?((?:sha256|sha512|sha1|blake3|md5)?(-|:)?[A-Za-z0-9+/=]+)('|$)",
    )

    for line in reversed(stderr.split("\n")):
        if match := regex.fullmatch(line):
            return match[2]
    return None


def nix_prefetch(opts: Options, attr: str | None) -> str:
    expr = opts.get_package()

    if attr is not None:
        expr += f".{attr}"

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
        got = extract_hash_from_nix_error(stderr)
    finally:
        if tempdir:
            tempdir.cleanup()

    if got is None:
        tail = "\n".join(stderr.splitlines()[-20:])
        msg = (
            f"failed to retrieve hash when trying to update {opts.attribute}.{attr}\n"
            f"--- nix stderr (last 20 lines) ---\n{tail}"
        )
        raise UpdateError(msg)
    return got


def update_hash_with_prefetch(
    attr_name: str | None,
    opts: Options,
    filename: str,
    current_hash: str,
) -> None:
    """Generic function to update a hash by prefetching with a specific attribute."""
    target_hash = nix_prefetch(opts, attr_name)
    replace_hash(filename, current_hash, target_hash)


# Create partial function for updating src hash (used elsewhere in the code)
update_src_hash = partial(update_hash_with_prefetch, "src")


def build_package_attr(opts: Options, attr: str) -> str:
    """Build a package attribute and return the resulting store path.

    Uses ``opts.get_package()`` instead of ``nix-build -A`` because flake
    repositories may not have a default.nix.
    """
    return run(
        [
            "nix-build",
            "--expr",
            f"{opts.get_package()}.{attr}",
            "--no-out-link",
            *opts.extra_flags,
        ],
    ).stdout.strip()


def update_nuget_deps(opts: Options) -> None:
    """Update NuGet dependencies."""
    fetch_deps_script_path = build_package_attr(opts, "fetch-deps")

    cmd = [fetch_deps_script_path]
    flake_src = opts.get_flake_import_path()
    if flake_src is not None:
        # The script's default deps file points into the read-only store copy
        # of the flake source; redirect it to the local checkout.
        match = re.search(
            r"^defaultDepsFile=(.*)$",
            Path(fetch_deps_script_path).read_text(),
            re.MULTILINE,
        )
        deps_file = match.group(1).strip("'\"") if match else ""
        prefix = flake_src.rstrip("/") + "/"
        if deps_file.startswith(prefix):
            cmd.append(str(Path(opts.import_path) / deps_file.removeprefix(prefix)))

    # Without an argument the script writes to its default deps file
    run(cmd)


def update_gradle_mitm_cache(opts: Options) -> None:
    """Update Gradle dependencies."""
    update_script_path = build_package_attr(opts, "mitmCache.updateScript")

    run([update_script_path])


def update_npm_deps(opts: Options, filename: str, old_hash: str) -> None:
    if opts.generate_lockfile:
        generate_lockfile(opts, filename, "npm", opts.get_package())
    update_hash_with_prefetch("npmDeps", opts, filename, old_hash)


def update_dependency_hashes(
    opts: Options,
    package: Package,
    *,
    update_hash: bool,
) -> None:
    if not (update_hash or not package.hash) or opts.src_only:
        return

    hash_updaters: dict[str, Callable[[Options, str, Any], None]] = {
        "fod_subpackage": partial(update_hash_with_prefetch, None),
        "go_modules": partial(update_hash_with_prefetch, "goModules"),
        "go_modules_old": partial(update_hash_with_prefetch, "go-modules"),
        "cargo_deps": partial(update_hash_with_prefetch, "cargoDeps"),
        "cargo_vendor_deps": partial(
            update_hash_with_prefetch,
            "cargoDeps.vendorStaging",
        ),
        "composer_deps": partial(update_hash_with_prefetch, "composerVendor"),
        "composer_deps_old": partial(update_hash_with_prefetch, "composerRepository"),
        "npm_deps": update_npm_deps,
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

    # Handle gradle mitm cache separately since it's a boolean
    if package.has_gradle_mitm_cache:
        update_gradle_mitm_cache(opts)

    # Handle custom deps
    if package.custom_deps:
        for custom_dep in package.custom_deps:
            for drv_name, old_hash in custom_dep.items():
                update_hash_with_prefetch(drv_name, opts, package.filename, old_hash)
