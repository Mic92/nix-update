from __future__ import annotations

import json
import os
from dataclasses import InitVar, dataclass, field
from textwrap import dedent, indent
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import ParseResult, urlparse

from .errors import UpdateError
from .utils import run
from .version.version import Version, VersionPreference

if TYPE_CHECKING:
    from .options import Options


@dataclass
class Position:
    file: str
    line: int
    column: int


class CargoLock:
    pass


class CargoLockInSource(CargoLock):
    def __init__(self, path: str) -> None:
        self.path = path


class CargoLockInStore(CargoLock):
    pass


@dataclass
class Package:
    attribute: str
    import_path: InitVar[str]
    name: str
    pname: str
    old_version: str
    filename: str
    line: int
    urls: list[str] | None
    url: str | None
    src_homepage: str | None
    changelog: str | None
    maintainers: list[dict[str, str]] | None
    rev: str | None
    tag: str | None
    hash: str | None
    go_modules: str | None
    go_modules_old: str | None
    cargo_deps: str | None
    cargo_vendor_deps: str | None
    npm_deps: str | None
    pnpm_deps: str | None
    yarn_deps: str | None
    yarn_deps_old: str | None
    composer_deps: str | None
    composer_deps_old: str | None
    maven_deps: str | None
    mix_deps: str | None
    zig_deps: str | None
    has_nuget_deps: bool
    tests: list[str]
    has_update_script: bool

    raw_version_position: InitVar[dict[str, Any] | None]
    raw_cargo_lock: InitVar[Literal[False] | str | None]

    parsed_url: ParseResult | None = None
    new_version: Version | None = None
    version_position: Position | None = field(init=False)
    cargo_lock: CargoLock | None = field(init=False)
    diff_url: str | None = None

    def __post_init__(
        self,
        import_path: str,
        raw_version_position: dict[str, Any] | None,
        raw_cargo_lock: Literal[False] | str | None,
    ) -> None:
        url = self.url or (self.urls[0] if self.urls else None)
        if url:
            self.parsed_url = urlparse(url)
        if raw_version_position is None:
            self.version_position = None
        else:
            self.version_position = Position(**raw_version_position)
            if self.filename:
                self.version_position.file = self.filename

        if raw_cargo_lock is None:
            self.cargo_lock = None
        elif raw_cargo_lock is False or not os.path.realpath(raw_cargo_lock).startswith(
            import_path,
        ):
            self.cargo_lock = CargoLockInStore()
        else:
            self.cargo_lock = CargoLockInSource(raw_cargo_lock)


def eval_expression(
    escaped_import_path: str,
    attr: str,
    *,
    flake: bool,
    system: str | None,
    override_filename: str | None,
) -> str:
    system = f'"{system}"' if system else "builtins.currentSystem"

    if flake:
        sanitize_position = (
            f"""
              sanitizePosition = {{ file, ... }}@pos:
                assert substring 0 outPathLen file != outPath
                  -> throw "${{file}} is not in ${{outPath}}";
                pos // {{ file = {escaped_import_path} + substring outPathLen (stringLength file - outPathLen) file; }};
            """
            if override_filename is None
            else """
              sanitizePosition = x: x;
            """
        ).strip()

        let_bindings = f"""
          inherit (builtins) getFlake stringLength substring;
          currentSystem = {system};
          flake = getFlake {escaped_import_path};
          pkg = flake.packages.${{currentSystem}}.{attr} or flake.{attr};
          inherit (flake) outPath;
          outPathLen = stringLength outPath;
          {sanitize_position}
        """
    else:
        let_bindings = f"""
          pkgs = import {escaped_import_path};
          args =  builtins.functionArgs pkgs;
          inputs = (if args ? system then {{ system = {system}; }} else {{}}) //
                   (if args ? overlays then {{ overlays = [ ]; }} else {{}});
          pkg = (pkgs inputs).{attr};
          sanitizePosition = x: x;
        """

    has_update_script = "pkg.passthru.updateScript or null != null"

    return f"""
let
  {indent(dedent(let_bindings), "  ")}
  positionFromMeta = pkg: let
    parts = builtins.match "(.*):([0-9]+)" pkg.meta.position;
  in {{
    file = builtins.elemAt parts 0;
    line = builtins.fromJSON (builtins.elemAt parts 1);
  }};

  raw_version_position = sanitizePosition (builtins.unsafeGetAttrPos "version" pkg);

  position = if pkg ? isRubyGem then
    raw_version_position
  else if pkg ? isPhpExtension then
    raw_version_position
  else if (builtins.unsafeGetAttrPos "src" pkg) != null then
    sanitizePosition (builtins.unsafeGetAttrPos "src" pkg)
  else
    sanitizePosition (positionFromMeta pkg);
in {{
  name = pkg.name;
  pname = pkg.pname;
  old_version = pkg.version or (builtins.parseDrvName pkg.name).version;
  inherit raw_version_position;
  filename = position.file;
  line = position.line;
  urls = pkg.src.urls or null;
  url = pkg.src.url or null;
  rev = pkg.src.rev or null;
  tag = pkg.src.tag or null;
  hash = pkg.src.outputHash or null;
  go_modules = pkg.goModules.outputHash or null;
  go_modules_old = pkg.go-modules.outputHash or null;
  cargo_deps = pkg.cargoDeps.outputHash or null;
  cargo_vendor_deps = pkg.cargoDeps.vendorStaging.outputHash or null;
  raw_cargo_lock =
    if pkg ? cargoDeps.lockFile then
      let
        inherit (pkg.cargoDeps) lockFile;
        res = builtins.tryEval (sanitizePosition {{
          file = toString lockFile;
        }});
      in
      if res.success then res.value.file else false
    else
      null;
  composer_deps = pkg.composerVendor.outputHash or null;
  composer_deps_old = pkg.composerRepository.outputHash or null;
  npm_deps = pkg.npmDeps.outputHash or null;
  pnpm_deps = pkg.pnpmDeps.outputHash or null;
  yarn_deps = pkg.yarnOfflineCache.outputHash or null;
  yarn_deps_old = pkg.offlineCache.outputHash or null;
  maven_deps = pkg.fetchedMavenDeps.outputHash or null;
  has_nuget_deps = pkg ? nugetDeps;
  mix_deps = pkg.mixFodDeps.outputHash or null;
  zig_deps = pkg.zigDeps.outputHash or null;
  tests = builtins.attrNames (pkg.passthru.tests or {{}});
  has_update_script = {has_update_script};
  src_homepage = pkg.src.meta.homepage or null;
  changelog = pkg.meta.changelog or null;
  maintainers = pkg.meta.maintainers or null;
}}"""


def eval_attr(opts: Options) -> Package:
    expr = eval_expression(
        opts.escaped_import_path,
        opts.escaped_attribute,
        flake=opts.flake,
        system=opts.system,
        override_filename=opts.override_filename,
    )
    cmd = ["nix", "--extra-experimental-features", "nix-command", "eval", "--json", "--impure", "--expr", expr, *opts.extra_flags]
    res = run(cmd)
    out = json.loads(res.stdout)
    if opts.override_filename is not None:
        out["filename"] = opts.override_filename
    if opts.url is not None:
        out["url"] = opts.url
    package = Package(attribute=opts.attribute, import_path=opts.import_path, **out)
    if opts.version_preference != VersionPreference.SKIP and package.old_version == "":
        msg = f"Nix's builtins.parseDrvName could not parse the version from {package.name}"
        raise UpdateError(msg)

    return package
