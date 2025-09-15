"""Cargo lock update functionality for nix-update."""

from __future__ import annotations

import fileinput
import re
import shutil
import tempfile
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

from .eval import CargoLock, CargoLockInSource, CargoLockInStore
from .git import git_prefetch
from .lockfile import generate_lockfile
from .utils import run

if TYPE_CHECKING:
    from .options import Options


def _build_cargo_lock(opts: Options, tempdir: str) -> Path | None:
    res = run(
        [
            "nix",
            "build",
            "--out-link",
            f"{tempdir}/result",
            "--impure",
            "--print-out-paths",
            "--expr",
            f'\n{opts.get_package()}.overrideAttrs (old: {{\n  cargoDeps = null;\n  postUnpack = \'\'\n    cp -r "$sourceRoot/${{old.cargoRoot or "."}}/Cargo.lock" $out\n    exit\n  \'\';\n  outputs = [ "out" ];\n  separateDebugInfo = false;\n}})\n',
            *opts.extra_flags,
        ],
    )
    src = Path(res.stdout.strip())
    return src if src.is_file() else None


def _process_git_dependencies(lock: dict) -> dict[str, str]:
    regex = re.compile(r"git\+([^?]+)(\?(rev|tag|branch)=.*)?#(.*)")
    git_deps = {}
    for pkg in lock["package"]:
        if (source := pkg.get("source")) and (match := regex.fullmatch(source)):
            rev = match[4]
            if rev not in git_deps:
                git_deps[rev] = f"{pkg['name']}-{pkg['version']}", match[1]

    return dict(ThreadPoolExecutor().map(git_prefetch, git_deps.items()))


def _update_short_format(
    hashes: dict[str, str],
    match: re.Match[str],
    f: fileinput.FileInput[str],
) -> None:
    indent = match[1]
    print(match[0], end="")
    _print_hashes(hashes, indent)
    for line in f:
        print(line, end="")


def _update_expanded_format(
    hashes: dict[str, str],
    match: re.Match[str],
    f: fileinput.FileInput[str],
) -> None:
    indent = match[1]
    print(match[0], end="")
    _print_hashes(hashes, indent)
    brace = 0
    for next_line in f:
        for c in next_line:
            if c == "{":
                brace -= 1
            if c == "}":
                brace += 1
            if brace == 1:
                print(next_line, end="")
                for final_line in f:
                    print(final_line, end="")
                return


def _print_hashes(hashes: dict[str, str], indent: str) -> None:
    if not hashes:
        return
    print(f"{indent}outputHashes = {{")
    for k, v in hashes.items():
        print(f'{indent}  "{k}" = "{v}";')
    print(f"{indent}}};")


def _update_cargo_lock(
    opts: Options,
    filename: str,
    dst: CargoLockInSource | CargoLockInStore,
) -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        src = _build_cargo_lock(opts, tempdir)
        if not src:
            return

        hashes = {}
        with Path(src).open("rb") as f:
            if isinstance(dst, CargoLockInSource):
                with Path(dst.path).open("wb") as fdst:
                    shutil.copyfileobj(f, fdst)

                with Path(dst.path).open("rb") as fdst:
                    f.seek(0)
                    lock = tomllib.load(fdst) if fdst else tomllib.load(f)
            else:
                with Path(f"{tempdir}/Cargo.lock").open("wb") as ftemp:
                    shutil.copyfileobj(f, ftemp)
                    ftemp.flush()
                    f.seek(0)

            lock = tomllib.load(f)
            hashes = _process_git_dependencies(lock)

    with fileinput.FileInput(filename, inplace=True) as f:
        short = re.compile(r"(\s*)cargoLock\.lockFile\s*=\s*(.+)\s*;\s*")
        expanded = re.compile(r"(\s*)lockFile\s*=\s*(.+)\s*;\s*")

        for line in f:
            if match := short.fullmatch(line):
                _update_short_format(hashes, match, f)
                return
            if match := expanded.fullmatch(line):
                _update_expanded_format(hashes, match, f)
                return
            print(line, end="")


def update_cargo_lock(
    opts: Options,
    filename: str,
    cargo_lock: CargoLock | None,
) -> None:
    """Handle cargo lock updates with optional lockfile generation."""
    if cargo_lock is None or not isinstance(
        cargo_lock,
        CargoLockInSource | CargoLockInStore,
    ):
        return

    if opts.generate_lockfile:
        generate_lockfile(opts, filename, "cargo", opts.get_package())
    else:
        _update_cargo_lock(opts, filename, cargo_lock)
