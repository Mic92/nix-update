from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from nix_update.git import old_version_from_diff, old_version_from_git

if TYPE_CHECKING:
    import pytest

    from tests import conftest

TEST_ROOT = Path(__file__).parent.resolve()


def test_worddiff(helpers: conftest.Helpers) -> None:
    with helpers.root().joinpath("consul.patch").open() as f:
        diff = f.read()
        s = old_version_from_diff(diff, 5, "1.9.0")
        assert s == "1.8.6"


def test_old_version_from_git_outside_cwd_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The file's own repository must be used, not the current working directory."""
    cwd_repo = tmp_path / "cwd-repo"
    pkg_repo = tmp_path / "pkg-repo"
    cwd_repo.mkdir()
    pkg_repo.mkdir()
    for repo in (cwd_repo, pkg_repo):
        subprocess.run(["git", "-C", repo, "init", "-q"], check=True)

    pkg_file = pkg_repo / "package.nix"
    pkg_file.write_text('{\n  version = "1.0.0";\n}\n')
    subprocess.run(["git", "-C", pkg_repo, "add", "package.nix"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            pkg_repo,
            "-c",
            "user.name=nix-update",
            "-c",
            "user.email=nix-update@example.com",
            "commit",
            "-q",
            "-m",
            "init",
            "--no-gpg-sign",
        ],
        check=True,
    )
    pkg_file.write_text('{\n  version = "2.0.0";\n}\n')

    monkeypatch.chdir(cwd_repo)
    assert old_version_from_git(str(pkg_file), 2, "2.0.0") == "1.0.0"


def test_old_version_from_git_no_repo(tmp_path: Path) -> None:
    pkg_file = tmp_path / "package.nix"
    pkg_file.write_text('version = "2.0.0";\n')
    assert old_version_from_git(str(pkg_file), 1, "2.0.0") is None
