from __future__ import annotations

import json
import os
from dataclasses import InitVar, dataclass, field
from pathlib import Path
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
    fod_subpackage: str | None
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
    has_gradle_mitm_cache: bool
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


def get_eval_nix_path() -> Path:
    """Get the path to the eval.nix file."""
    return Path(__file__).parent / "eval.nix"


def eval_attr(opts: Options) -> Package:
    eval_nix = get_eval_nix_path()

    # Pass the attribute path as JSON string
    attribute_json = json.dumps(opts.attribute_path)

    # Build nix-instantiate command with --arg and --argstr
    cmd = [
        "nix-instantiate",
        "--eval",
        "--json",
        "--strict",
        str(eval_nix),
        "--argstr",
        "importPath",
        opts.import_path,
        "--argstr",
        "attribute",
        attribute_json,
        "--arg",
        "isFlake",
        "true" if opts.flake else "false",
        "--arg",
        "sanitizePositions",
        "false" if opts.override_filename else "true",
    ]

    if opts.system:
        cmd.extend(["--argstr", "system", opts.system])

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
