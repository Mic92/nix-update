import fileinput
import re
import json
from typing import List

from .utils import run, info
from .errors import UpdateError
from .version import fetch_latest_version
from .options import Options


def eval_attr(import_path: str, attr: str) -> str:
    return f"""(with import {import_path} {{}};
    let
      pkg = {attr};
    in {{
      name = pkg.name;
      version = (builtins.parseDrvName pkg.name).version;
      position = pkg.meta.position;
      urls = pkg.src.urls or null;
      url = pkg.src.url or null;
      hash = pkg.src.outputHash;
      modSha256 = pkg.modSha256 or null;
      cargoSha256 = pkg.cargoSha256 or null;
    }})"""


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


def update_cargoSha256_hash(opts: Options, filename: str, current_hash: str) -> None:
    expr = f"{{ sha256 }}: (import {opts.import_path} {{}}).{opts.attribute}.cargoDeps.overrideAttrs (_: {{ inherit sha256; }})"
    target_hash = nix_prefetch([expr])
    replace_hash(filename, current_hash, target_hash)


def update(opts: Options) -> None:
    res = run(["nix", "eval", "--json", eval_attr(opts.import_path, opts.attribute)])
    out = json.loads(res.stdout)
    current_version: str = out["version"]
    if current_version == "":
        name = out["name"]
        raise UpdateError(
            f"Nix's builtins.parseDrvName could not parse the version from {name}"
        )
    filename, line = out["position"].rsplit(":", 1)

    if opts.version != "skip":
        if opts.version == "auto":
            # latest_version = find_repology_release(attr)
            # if latest_version is None:
            url = out.get("url", None)
            urls = out.get("urls", None)
            if not url:
                if urls:
                    url = urls[0]
                else:
                    raise UpdateError(
                        "Could not find a url in the derivations src attribute"
                    )
            target_version = fetch_latest_version(url)
        else:
            target_version = opts.version
        update_version(filename, current_version, target_version)

    update_src_hash(opts, filename, out["hash"])

    if out["modSha256"]:
        update_mod256_hash(opts, filename, out["modSha256"])

    if out["cargoSha256"]:
        update_cargoSha256_hash(opts, filename, out["cargoSha256"])
