from dataclasses import dataclass
from typing import Optional, List
import json

from .utils import run
from .options import Options
from .errors import UpdateError


@dataclass
class Package:
    name: str
    old_version: str
    filename: str
    line: int
    urls: Optional[List[str]]
    url: Optional[str]
    rev: str
    hash: str
    mod_sha256: Optional[str]
    cargo_sha256: Optional[str]

    new_version: Optional[str] = None


def eval_expression(import_path: str, attr: str) -> str:
    return f"""(with import {import_path} {{}};
    let
      pkg = {attr};
    in {{
      name = pkg.name;
      old_version = (builtins.parseDrvName pkg.name).version;
      position = pkg.meta.position;
      urls = pkg.src.urls or null;
      url = pkg.src.url or null;
      rev = pkg.src.url.rev or null;
      hash = pkg.src.outputHash;
      mod_sha256 = pkg.modSha256 or null;
      cargo_sha256 = pkg.cargoSha256 or null;
    }})"""


def eval_attr(opts: Options) -> Package:
    res = run(
        ["nix", "eval", "--json", eval_expression(opts.import_path, opts.attribute)]
    )
    out = json.loads(res.stdout)

    filename, line = out["position"].rsplit(":", 1)
    del out["position"]

    package = Package(filename=filename, line=int(line), **out)
    if package.old_version == "":
        raise UpdateError(
            f"Nix's builtins.parseDrvName could not parse the version from {package.name}"
        )

    return package
