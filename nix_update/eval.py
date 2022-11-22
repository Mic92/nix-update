import json
from dataclasses import InitVar, dataclass, field
from typing import Any, Dict, List, Optional

from .errors import UpdateError
from .options import Options
from .utils import run
from .version.version import Version, VersionPreference


@dataclass
class Position:
    file: str
    line: int
    column: int


@dataclass
class Package:
    attribute: str
    name: str
    old_version: str
    filename: str
    line: int
    urls: Optional[List[str]]
    url: Optional[str]
    changelog: Optional[str]
    rev: str
    hash: Optional[str]
    vendor_hash: Optional[str]
    vendor_sha256: Optional[str]
    cargo_deps: Optional[str]
    npm_deps: Optional[str]
    tests: List[str]

    raw_version_position: InitVar[Optional[Dict[str, Any]]]

    new_version: Optional[Version] = None
    version_position: Optional[Position] = field(init=False)

    def __post_init__(self, raw_version_position: Optional[Dict[str, Any]]) -> None:
        if raw_version_position is None:
            self.version_position = None
        else:
            self.version_position = Position(**raw_version_position)


def eval_expression(import_path: str, attr: str) -> str:
    return f"""(
    let
      inputs = (if (builtins.hasAttr "overlays" (builtins.functionArgs (import {import_path}))) then {{ overlays = []; }} else {{ }});
    in
    with import {import_path} inputs;
    let
      pkg = {attr};
      raw_version_position = builtins.unsafeGetAttrPos "version" pkg;

      position = if pkg ? isRubyGem then
        raw_version_position
      else
        builtins.unsafeGetAttrPos "src" pkg;
    in {{
      name = pkg.name;
      old_version = pkg.version or (builtins.parseDrvName pkg.name).version;
      inherit raw_version_position;
      filename = position.file;
      line = position.line;
      urls = pkg.src.urls or null;
      url = pkg.src.url or null;
      rev = pkg.src.rev or null;
      hash = pkg.src.outputHash or null;
      vendor_hash = pkg.vendorHash or null;
      vendor_sha256 = pkg.vendorSha256 or null;
      cargo_deps = (pkg.cargoDeps or null).outputHash or null;
      npm_deps = (pkg.npmDeps or null).outputHash or null;
      tests = builtins.attrNames (pkg.passthru.tests or {{}});
      changelog = pkg.meta.changelog or null;
    }})"""


def eval_attr(opts: Options) -> Package:
    expr = eval_expression(opts.import_path, opts.attribute)
    cmd = [
        "nix",
        "eval",
        "--json",
        "--impure",
        "--extra-experimental-features",
        "nix-command",
        "--expr",
        expr,
    ]
    res = run(cmd)
    out = json.loads(res.stdout)
    package = Package(attribute=opts.attribute, **out)
    if opts.override_filename is not None:
        package.filename = opts.override_filename
    if opts.version_preference != VersionPreference.SKIP and package.old_version == "":
        raise UpdateError(
            f"Nix's builtins.parseDrvName could not parse the version from {package.name}"
        )

    return package
