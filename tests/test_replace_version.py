from __future__ import annotations

from pathlib import Path

from nix_update.eval import eval_attr
from nix_update.options import Options
from nix_update.update import replace_version
from nix_update.version.version import Version


def test_same_version_without_rev_is_noop(testpkgs: Path) -> None:
    # fetchurl-github-release pins neither rev nor tag, so a rev reported by
    # the version fetcher has nothing to rewrite and must not count as a change.
    package = eval_attr(
        Options(attribute="fetchurl-github-release", import_path=str(testpkgs)),
    )
    assert package.rev is None
    assert package.tag is None
    package.new_version = Version(package.old_version, rev="deadbeef")
    before = Path(package.filename).read_text()

    assert not replace_version(package)
    assert Path(package.filename).read_text() == before
