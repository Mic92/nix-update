"""Cargo lock update functionality for nix-update."""

from __future__ import annotations

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
from .nix_ast import Edit, apply_edits, bindings, parse, whole_lines
from .utils import run

if TYPE_CHECKING:
    from ast_grep_py import SgNode

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


def _is_cargo_lock(lock_file: SgNode) -> bool:
    """Whether ``lockFile`` sits in ``cargoLock = { }`` or ``importCargoLock { }``."""
    attrs = lock_file.parent()
    owner = attrs.parent() if attrs else None
    if owner and owner.kind() == "attrset_expression":
        owner = owner.parent()
    return owner is not None and owner.text().startswith(
        ("cargoLock", "cargoDeps", "rustPlatform.importCargoLock", "importCargoLock")
    )


def set_output_hashes(text: str, hashes: dict[str, str]) -> str:
    """Replace the outputHashes next to a cargo ``lockFile`` binding."""
    root = parse(text)
    if root is None:
        return text
    prefix = "cargoLock."
    lock_files = bindings(root, "cargoLock.lockFile")
    if not lock_files:
        prefix = ""
        lock_files = bindings(root, "lockFile")
        lock_files.sort(key=_is_cargo_lock, reverse=True)
    attrs = lock_files[0].parent() if lock_files else None
    if attrs is None:
        return text
    lock_file = lock_files[0]

    rng = lock_file.range()
    line = text.splitlines()[rng.start.line]
    indent = line[: len(line) - len(line.lstrip())]
    if line[: rng.start.column].strip():
        # shares its line with the opening brace
        indent += "  "
    entries = "".join(f'{indent}  "{k}" = "{v}";\n' for k, v in hashes.items())
    new = f"{prefix}outputHashes = {{\n{entries}{indent}}};" if hashes else ""

    # Reuse the place of the existing binding so surrounding comments stay put
    edits: list[Edit] = []
    for old in bindings(attrs, f"{prefix}outputHashes", nested=True):
        span = old.range().start.index, old.range().end.index
        edits.append((*span, new) if new else (*whole_lines(text, *span), ""))
        new = ""
    if new:
        edits.append((rng.end.index, rng.end.index, f"\n{indent}{new}"))
    return apply_edits(text, edits)


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

    path = Path(filename)
    path.write_text(set_output_hashes(path.read_text(), hashes))


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
