"""Lockfile generation utilities for nix-update."""

from __future__ import annotations

import shutil
import tempfile
import textwrap
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .errors import UpdateError
from .utils import run

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .options import Options


@dataclass
class LockfileConfig:
    """Configuration for different lockfile types."""

    cmd: list[str]
    bin_name: str
    lockfile_name: str
    extra_nix_override: str


def get_lockfile_config(lockfile_type: str, metadata_path: str) -> LockfileConfig:
    """Get configuration for the specified lockfile type."""
    configs = {
        "cargo": LockfileConfig(
            cmd=[
                "generate-lockfile",
                "--manifest-path",
                f"{metadata_path}/Cargo.toml",
            ],
            bin_name="cargo",
            lockfile_name="Cargo.lock",
            extra_nix_override="""
          cargoDeps = null;
          cargoVendorDir = ".";
        """,
        ),
        "npm": LockfileConfig(
            cmd=[
                "install",
                "--package-lock-only",
                "--prefix",
                metadata_path,
            ],
            bin_name="npm",
            lockfile_name="package-lock.json",
            extra_nix_override="""
          npmDeps = null;
          npmDepsHash = null;
        """,
        ),
    }

    if lockfile_type not in configs:
        msg = f"Unsupported lockfile type: {lockfile_type}. Supported types are: {', '.join(configs.keys())}."
        raise UpdateError(msg)

    return configs[lockfile_type]


@contextmanager
def disable_copystat() -> Iterator[None]:
    """Temporarily disable shutil.copystat to avoid permission issues."""
    _orig = shutil.copystat
    shutil.copystat = lambda *_args, **_kwargs: None
    try:
        yield
    finally:
        shutil.copystat = _orig


def build_source_with_tool(
    opts: Options,
    package_expr: str,
    config: LockfileConfig,
) -> Path:
    """Build the source and extract the tool binary path."""
    get_src_and_bin = textwrap.dedent(
        f"""
      {package_expr}.overrideAttrs (old: {{
        {config.extra_nix_override}
        postUnpack = ''
          cp -pr --reflink=auto -- $sourceRoot $out
          mkdir -p "$out/nix-support"
          command -v {config.bin_name} > $out/nix-support/{config.bin_name}-bin || {{
            echo "no {config.bin_name} executable found in native build inputs" >&2
            exit 1
          }}
          exit
        '';
        outputs = [ "out" ];
        separateDebugInfo = false;
      }})
    """,
    )

    res = run(
        [
            "nix",
            "build",
            "-L",
            "--no-link",
            "--impure",
            "--print-out-paths",
            "--expr",
            get_src_and_bin,
            *opts.extra_flags,
        ],
    )
    return Path(res.stdout.strip())


def resolve_lockfile_path(tempdir: str, metadata_path: str, lockfile_name: str) -> Path:
    """Resolve the actual path of the generated lockfile."""
    lockfile_in_subdir = Path(tempdir) / metadata_path / lockfile_name
    if lockfile_in_subdir.exists():
        return lockfile_in_subdir
    return Path(tempdir) / lockfile_name


def generate_lockfile(
    opts: Options,
    filename: str,
    lockfile_type: str,
    package_expr: str,
) -> None:
    """Generate a lockfile for the specified package.

    Args:
        opts: Options for the update operation
        filename: Path to the package file being updated
        lockfile_type: Type of lockfile to generate ("cargo" or "npm")
        package_expr: Nix expression to get the package
    """
    config = get_lockfile_config(lockfile_type, opts.lockfile_metadata_path)
    src = build_source_with_tool(opts, package_expr, config)

    with tempfile.TemporaryDirectory() as tempdir:
        # Copy source to temp directory
        with disable_copystat():
            shutil.copytree(src, tempdir, dirs_exist_ok=True, copy_function=shutil.copy)

        # Make any existing lockfile writable (files from Nix store are read-only)
        lockfile = resolve_lockfile_path(
            tempdir,
            opts.lockfile_metadata_path,
            config.lockfile_name,
        )
        if lockfile.exists():
            lockfile.chmod(lockfile.stat().st_mode | 0o200)

        # Get tool binary path and run lockfile generation
        bin_path = (
            (src / "nix-support" / f"{config.bin_name}-bin").read_text().rstrip("\n")
        )
        run([bin_path, *config.cmd], cwd=tempdir)

        # Find where the lockfile was generated
        lockfile = resolve_lockfile_path(
            tempdir,
            opts.lockfile_metadata_path,
            config.lockfile_name,
        )

        # Copy lockfile to the package directory
        shutil.copy(lockfile, Path(filename).parent / config.lockfile_name)
