import fileinput
import re
import json
from typing import List, Optional

from .utils import run
from .errors import UpdateError
from .version import fetch_latest_version


def eval_attr(import_path: str, attr: str) -> str:
    return f"""(with import {import_path} {{}};
    let
      pkg = {attr};
    in {{
      name = pkg.name;
      version = (builtins.parseDrvName pkg.name).version;
      position = pkg.meta.position;
      urls = pkg.src.urls;
      hash = pkg.src.outputHash;
      modSha256 = pkg.modSha256 or null;
      cargoSha256 = pkg.cargoSha256 or null;
    }})"""


def update_version(filename: str, current: str, target: str) -> None:
    if target.startswith("v"):
        target = target[1:]

    if current != target:
        with fileinput.FileInput(filename, inplace=True) as f:
            for line in f:
                print(line.replace(current, target), end="")


def replace_hash(filename: str, current: str, target: str) -> None:
    if current != target:
        with fileinput.FileInput(filename, inplace=True) as f:
            for line in f:
                line = re.sub(current, target, line)
                print(line, end="")


def nix_prefetch(cmd: List[str]) -> str:
    res = run(["nix-prefetch"] + cmd)
    return res.stdout.strip()


def update_src_hash(
    import_path: str, attr: str, filename: str, current_hash: str
) -> None:
    target_hash = nix_prefetch([f"(import {import_path} {{}}).{attr}"])
    replace_hash(filename, current_hash, target_hash)


def update_mod256_hash(
    import_path: str, attr: str, filename: str, current_hash: str
) -> None:
    expr = f"{{ sha256 }}: (import {import_path} {{}}).{attr}.go-modules.overrideAttrs (_: {{ modSha256 = sha256; }})"
    target_hash = nix_prefetch([expr])
    replace_hash(filename, current_hash, target_hash)


def update_cargoSha256_hash(
    import_path: str, attr: str, filename: str, current_hash: str
) -> None:
    expr = f"{{ sha256 }}: (import {import_path} {{}}).{attr}.cargoDeps.overrideAttrs (_: {{ inherit sha256; }})"
    target_hash = nix_prefetch([expr])
    replace_hash(filename, current_hash, target_hash)


def update(import_path: str, attr: str, target_version: Optional[str]) -> None:
    res = run(["nix", "eval", "--json", eval_attr(import_path, attr)])
    out = json.loads(res.stdout)
    current_version: str = out["version"]
    if current_version == "":
        name = out["name"]
        UpdateError(
            f"Nix's builtins.parseDrvName could not parse the version from {name}"
        )
    filename, line = out["position"].rsplit(":", 1)

    if not target_version:
        # latest_version = find_repology_release(attr)
        # if latest_version is None:
        url = out["urls"][0]
        target_version = fetch_latest_version(url)
    update_version(filename, current_version, target_version)

    update_src_hash(import_path, attr, filename, out["hash"])

    if out["modSha256"]:
        update_mod256_hash(import_path, attr, filename, out["modSha256"])

    if out["cargoSha256"]:
        update_cargoSha256_hash(import_path, attr, filename, out["cargoSha256"])
