import json
from dataclasses import dataclass
from typing import List, Optional

from .errors import UpdateError
from .options import Options
from .utils import run


@dataclass
class Package:
    attribute: str
    name: str
    old_version: str
    filename: str
    line: int
    urls: Optional[List[str]]
    url: Optional[str]
    rev: str
    hash: str
    mod_sha256: Optional[str]
    vendor_sha256: Optional[str]
    cargo_sha256: Optional[str]
    tests: Optional[List[str]]

    new_version: Optional[str] = None


def eval_expression(import_path: str, attr: str) -> str:
    return f"""(with import {import_path} {{}};
    let
      pkg = {attr};
      position = if pkg ? isRubyGem then
        builtins.unsafeGetAttrPos "version" pkg
      else
        builtins.unsafeGetAttrPos "src" pkg;
    in {{
      name = pkg.name;
      old_version = (builtins.parseDrvName pkg.name).version;
      filename = position.file;
      line = position.line;
      urls = pkg.src.urls or null;
      url = pkg.src.url or null;
      rev = pkg.src.url.rev or null;
      hash = pkg.src.outputHash;
      mod_sha256 = pkg.modSha256 or null;
      vendor_sha256 = pkg.vendorSha256 or null;
      cargo_sha256 = pkg.cargoSha256 or null;
      tests = pkg.passthru.tests or null;
    }})"""


def eval_attr(opts: Options) -> Package:
    expr = eval_expression(opts.import_path, opts.attribute)
    cmd = [
        "nix",
        "eval",
        "--json",
        "--impure",
        "--experimental-features",
        "nix-command",
        "--expr",
        expr,
    ]
    res = run(cmd)
    out = json.loads(res.stdout)
    package = Package(attribute=opts.attribute, **out)
    if package.old_version == "":
        raise UpdateError(
            f"Nix's builtins.parseDrvName could not parse the version from {package.name}"
        )

    return package
