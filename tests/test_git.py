from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

import nix_update
from nix_update.git import old_version_from_diff, old_version_from_git

if TYPE_CHECKING:
    from tests import conftest

TEST_ROOT = Path(__file__).parent.resolve()
requires_jj = pytest.mark.skipif(
    shutil.which("jj") is None, reason="jj is not installed"
)


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


@requires_jj
@pytest.mark.parametrize("mode", ["--colocate", "--no-colocate"])
def test_jj_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    monkeypatch.setenv("JJ_USER", "nix-update")
    monkeypatch.setenv("JJ_EMAIL", "test@example.com")

    def jj(*args: str) -> str:
        return subprocess.check_output(["jj", *args], cwd=tmp_path, text=True)

    jj("git", "init", mode)
    package_dir = tmp_path / "pkgs (test)[1]"
    package_dir.mkdir()
    package_file = package_dir / "package.nix"
    package_file.write_text("old\n")
    jj("commit", "--message", "initial")
    (tmp_path / "unrelated").write_text("keep in working copy\n")

    def update(_options: object) -> SimpleNamespace:
        package_file.write_text("new\n")
        return SimpleNamespace(
            attribute="example",
            filename=str(package_file),
            old_version="1",
            new_version=SimpleNamespace(number="2", rev=None),
            cargo_lock=None,
            rev=None,
            diff_url=None,
            changelog=None,
            maintainers=None,
        )

    monkeypatch.setattr(nix_update, "update", update)
    args = ["--file", str(package_file), "--commit", "example"]
    nix_update.main(args)
    assert (
        jj("log", "--no-graph", "--revisions", "@-", "--template", "description")
        == "example: 1 -> 2\n"
    )
    assert (
        jj("diff", "--revision", "@-", "--summary") == "M pkgs (test)[1]/package.nix\n"
    )
    assert jj("diff", "--name-only") == "unrelated\n"

    revision_args = ("log", "--no-graph", "--revisions", "@", "--template", "commit_id")
    revision = jj(*revision_args)
    nix_update.main(args)
    assert jj(*revision_args) == revision


@requires_jj
def test_broken_jj_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".jj").mkdir()
    config = tmp_path / "broken.toml"
    config.write_text("[invalid")
    monkeypatch.setenv("JJ_CONFIG", str(config))

    assert nix_update.find_jj_root(str(tmp_path)) is None
    stderr = capsys.readouterr().err
    assert "broken.toml" in stderr
    assert "`jj root` failed; falling back to Git." in stderr
