"""Test that flake store path reflects current on-disk content.

Regression test for https://github.com/Mic92/nix-update/issues/537
After the version is updated in local files, evaluations (e.g. hash
prefetching) must see the new version — not a stale store copy from
before the update.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nix_update.eval import eval_attr
from nix_update.options import Options
from nix_update.update import update_version
from nix_update.version.version import VersionPreference

if TYPE_CHECKING:
    from pathlib import Path


def test_flake_store_path_reflects_version_update(testpkgs_git: Path) -> None:
    """get_flake_import_path() must return a different store path after a version change."""
    opts = Options(
        attribute="crate",
        flake=True,
        import_path=str(testpkgs_git),
        version="10.2.0",
        version_preference=VersionPreference.FIXED,
    )

    # Snapshot the store path before the update
    path_before = opts.get_flake_import_path()
    assert path_before is not None

    package = eval_attr(opts)

    # Update the version — modifies local files
    changed = update_version(
        opts,
        package,
        "10.2.0",
        VersionPreference.FIXED,
        "(.*)",
    )
    assert changed, "Version should have changed from 8.0.0 to 10.2.0"

    # The store path must now differ because the on-disk content changed
    path_after = opts.get_flake_import_path()
    assert path_after is not None
    assert path_after != path_before, (
        f"get_flake_import_path() returned the same store path before and after "
        f"the version update ({path_before}), so subsequent evaluations would "
        f"use stale content"
    )
