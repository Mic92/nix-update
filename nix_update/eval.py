import json
from dataclasses import InitVar, dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import ParseResult, urlparse

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
    src_homepage: Optional[str]
    changelog: Optional[str]
    rev: str
    hash: Optional[str]
    vendor_hash: Optional[str]
    vendor_sha256: Optional[str]
    cargo_deps: Optional[str]
    npm_deps: Optional[str]
    tests: List[str]
    has_update_script: bool

    raw_version_position: InitVar[Optional[Dict[str, Any]]]

    parsed_url: Optional[ParseResult] = None
    new_version: Optional[Version] = None
    version_position: Optional[Position] = field(init=False)
    diff_url: Optional[str] = None

    def __post_init__(self, raw_version_position: Optional[Dict[str, Any]]) -> None:
        url = self.url or (self.urls[0] if self.urls else None)
        if url:
            self.parsed_url = urlparse(url)
        if raw_version_position is None:
            self.version_position = None
        else:
            self.version_position = Position(**raw_version_position)


def eval_expression(
    import_path: str, attr: str, flake: bool, system: Optional[str]
) -> str:
    system = f'"{system}"' if system else "builtins.currentSystem"

    let_bindings = (
        f"""inherit (builtins) getFlake stringLength substring;
  currentSystem = {system};
  flake = getFlake "{import_path}";
  pkg = flake.packages.${{currentSystem}}.{attr} or flake.{attr};
  inherit (flake) outPath;
  outPathLen = stringLength outPath;
  sanitizePosition = {{ file, ... }}@pos:
    assert substring 0 outPathLen file == outPath;
    pos // {{ file = "{import_path}" + substring outPathLen (stringLength file - outPathLen) file; }};"""
        if flake
        else f"""
  inputs = if (builtins.functionArgs (import {import_path})) ? overlays then {{ overlays = [ ]; }} else {{ }};
  system = if (builtins.functionArgs (import {import_path})) ? system then {{ system = {system}; }} else {{ }};
  pkg = (import {import_path} (inputs // system)).{attr};
  sanitizePosition = x: x;"""
    )

    has_update_script = (
        "false" if flake else "pkg.passthru.updateScript or null != null"
    )

    return f"""
let
  {let_bindings}
  raw_version_position = sanitizePosition (builtins.unsafeGetAttrPos "version" pkg);

  position = if pkg ? isRubyGem then
    raw_version_position
  else if pkg ? isPhpExtension then
    raw_version_position
   else
    sanitizePosition (builtins.unsafeGetAttrPos "src" pkg);
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
  cargo_deps = pkg.cargoDeps.outputHash or null;
  npm_deps = pkg.npmDeps.outputHash or null;
  tests = builtins.attrNames (pkg.passthru.tests or {{}});
  has_update_script = {has_update_script};
  src_homepage = pkg.src.meta.homepage or null;
  changelog = pkg.meta.changelog or null;
}}"""


def eval_attr(opts: Options) -> Package:
    expr = eval_expression(opts.import_path, opts.attribute, opts.flake, opts.system)
    cmd = [
        "nix",
        "eval",
        "--json",
        "--impure",
        "--expr",
        expr,
    ] + opts.extra_flags
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
