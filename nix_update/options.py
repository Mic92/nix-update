from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from .errors import AttributePathError
from .version.version import VersionPreference


class ParseState(Enum):
    NORMAL = auto()
    QUOTED = auto()
    ESCAPED = auto()


def _validate_attribute_path(attribute: str) -> None:
    """Validate attribute path format."""
    if not attribute:
        msg = "Attribute path cannot be empty"
        raise AttributePathError(msg)
    if attribute.startswith("."):
        msg = f"Invalid attribute path: leading dot in '{attribute}'"
        raise AttributePathError(msg)


def parse_attribute_path(attribute: str) -> list[str]:
    """Parse an attribute path, handling quoted components and escaped quotes.

    Examples:
        "foo.bar" -> ["foo", "bar"]
        "foo.\"bar.baz\"" -> ["foo", "bar.baz"]
        "foo.\"bar\\\"baz\"" -> ["foo", "bar\"baz"]
        "cargoLock.update" -> ["cargoLock", "update"]

    Raises:
        AttributePathError: If the attribute path is invalid (e.g., trailing dots, unclosed quotes)
    """
    _validate_attribute_path(attribute)

    parts: list[str] = []
    current = ""
    state = ParseState.NORMAL
    prev_state = ParseState.NORMAL

    for char in attribute:
        if state == ParseState.ESCAPED:
            current += char
            state = prev_state
        elif char == "\\":
            prev_state = state
            state = ParseState.ESCAPED
        elif char == '"':
            current += char
            state = (
                ParseState.QUOTED if state == ParseState.NORMAL else ParseState.NORMAL
            )
        elif char == "." and state == ParseState.NORMAL:
            if not current:
                msg = f"Invalid attribute path: consecutive dots in '{attribute}'"
                raise AttributePathError(
                    msg,
                )
            parts.append(current.strip('"'))
            current = ""
        else:
            current += char

    if state == ParseState.QUOTED:
        msg = f"Invalid attribute path: unclosed quote in '{attribute}'"
        raise AttributePathError(
            msg,
        )
    if state == ParseState.ESCAPED:
        msg = f"Invalid attribute path: trailing escape in '{attribute}'"
        raise AttributePathError(
            msg,
        )
    if not current:
        msg = f"Invalid attribute path: trailing dot in '{attribute}'"
        raise AttributePathError(
            msg,
        )

    parts.append(current.strip('"'))
    return parts


def get_flake_store_path(import_path: str) -> str | None:
    """Copy a local flake into the Nix store and return its store path.

    Uses ``nix flake metadata`` so that git-ignored files are excluded and
    only tracked content is copied.  Returns *None* when the command fails
    (e.g. the directory is not a flake).
    """
    try:
        result = subprocess.run(
            ["nix", "flake", "metadata", "--json"],
            cwd=import_path,
            capture_output=True,
            text=True,
            check=True,
        )
        metadata = json.loads(result.stdout)
        return metadata.get("path")
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return None


@dataclass
class Options:
    attribute: str
    quiet: bool = False
    flake: bool = False
    version: str = "stable"
    version_preference: VersionPreference = VersionPreference.STABLE
    version_regex: str = "(.*)"
    import_path: str = str(Path.cwd())
    subpackages: list[str] | None = None
    override_filename: str | None = None
    url: str | None = None
    commit: bool = False
    use_update_script: bool = False
    update_script_args: list[str] = field(default_factory=list)
    print_commit_message: bool = False
    write_commit_message: str | None = None
    shell: bool = False
    run: bool = False
    build: bool = False
    test: bool = False
    review: bool = False
    format: bool = False
    system: str | None = None
    generate_lockfile: bool = False
    lockfile_metadata_path: str = "."
    src_only: bool = False
    update_src: bool = True
    use_github_releases: bool = False
    extra_flags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.attribute_path = parse_attribute_path(self.attribute)
        self.escaped_attribute = ".".join(map(json.dumps, self.attribute_path))
        self.escaped_import_path = json.dumps(self.import_path)

    def get_flake_import_path(self) -> str | None:
        """Get a fresh Nix store path for a local flake directory.

        Always re-copies the flake so the store path reflects the current
        on-disk content.  Returns *None* for non-flake packages or when
        the import path is not a local directory.
        """
        if not self.flake or not Path(self.import_path).is_dir():
            return None
        return get_flake_store_path(self.import_path)

    def get_package(self) -> str:
        """Get the Nix expression for the package."""
        import_path_to_use = self.escaped_import_path
        flake_store_path = self.get_flake_import_path()
        if flake_store_path is not None:
            import_path_to_use = json.dumps(flake_store_path)

        if self.flake:
            return f"(let flake = builtins.getFlake {import_path_to_use}; in flake.packages.${{builtins.currentSystem}}.{self.escaped_attribute} or flake.{self.escaped_attribute})"
        # Need to disable check meta for non-flake packages
        disable_check_meta = f'(if (builtins.hasAttr "config" (builtins.functionArgs (import {self.escaped_import_path}))) then {{ config.checkMeta = false; overlays = []; }} else {{ }})'
        return f"(import {self.escaped_import_path} {disable_check_meta}).{self.escaped_attribute}"
