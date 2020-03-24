import fileinput
import re
from typing import List

from .utils import run, info
from .errors import UpdateError
from .version import fetch_latest_version
from .options import Options
from .eval import eval_attr, Package


def update_version(package: Package) -> None:
    old_version = package.old_version
    new_version = package.new_version
    assert new_version is not None
    if new_version.startswith("v"):
        new_version = new_version[1:]

    if old_version != new_version:
        info(f"Update {old_version} -> {new_version} in {package.filename}")
        with fileinput.FileInput(package.filename, inplace=True) as f:
            for line in f:
                print(line.replace(old_version, new_version), end="")
    else:
        info(f"Not updating version, already {old_version}")


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


def update(opts: Options) -> Package:
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
            new_version = fetch_latest_version(url)
        else:
            new_version = opts.version
        package.new_version = new_version
        update_version(package)

    update_src_hash(opts, package.filename, package.hash)

    if package.mod_sha256:
        update_mod256_hash(opts, package.filename, package.mod_sha256)

    if package.cargo_sha256:
        update_cargo_sha256_hash(opts, package.filename, package.cargo_sha256)

    return package
