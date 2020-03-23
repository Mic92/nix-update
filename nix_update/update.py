import fileinput
import re
from typing import List

from .utils import run, info
from .errors import UpdateError
from .version import fetch_latest_version
from .options import Options
from .eval import eval_attr


def update_version(filename: str, current: str, target: str) -> None:
    if target.startswith("v"):
        target = target[1:]

    if current != target:
        info(f"Update {current} -> {target} in {filename}")
        with fileinput.FileInput(filename, inplace=True) as f:
            for line in f:
                print(line.replace(current, target), end="")
    else:
        info(f"Not updating version, already {current}")


def replace_hash(filename: str, current: str, target: str) -> None:
    if current != target:
        with fileinput.FileInput(filename, inplace=True) as f:
            for line in f:
                line = re.sub(current, target, line)
                print(line, end="")


def nix_prefetch(cmd: List[str]) -> str:
    res = run(["nix-prefetch"] + cmd)
    return res.stdout.strip()


def update_src_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch([f"(import {opts.import_path} {{}}).{opts.attribute}"])
    replace_hash(filename, current_hash, target_hash)


def update_mod256_hash(opts: Options, filename: str, current_hash: str) -> None:
    expr = f"{{ sha256 }}: (import {opts.import_path} {{}}).{opts.attribute}.go-modules.overrideAttrs (_: {{ modSha256 = sha256; }})"
    target_hash = nix_prefetch([expr])
    replace_hash(filename, current_hash, target_hash)


def update_cargo_sha256_hash(opts: Options, filename: str, current_hash: str) -> None:
    expr = f"{{ sha256 }}: (import {opts.import_path} {{}}).{opts.attribute}.cargoDeps.overrideAttrs (_: {{ inherit sha256; }})"
    target_hash = nix_prefetch([expr])
    replace_hash(filename, current_hash, target_hash)


def update(opts: Options) -> None:
    package = eval_attr(opts)

    if opts.version != "skip":
        if opts.version == "auto":
            if not package.url:
                if package.urls:
                    url = package.urls[0]
                else:
                    raise UpdateError(
                        "Could not find a url in the derivations src attribute"
                    )
            target_version = fetch_latest_version(url)
        else:
            target_version = opts.version
        update_version(package.filename, package.version, target_version)

    update_src_hash(opts, package.filename, package.hash)

    if package.mod_sha256:
        update_mod256_hash(opts, package.filename, package.mod_sha256)

    if package.cargo_sha256:
        update_cargo_sha256_hash(opts, package.filename, package.cargo_sha256)
