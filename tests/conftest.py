from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from nix_update.utils import nix_command

# Register vendored pytest-shard plugin
pytest_plugins = ["tests.pytest_shard.pytest_shard"]

if TYPE_CHECKING:
    from collections.abc import Iterator

TEST_ROOT = Path(__file__).parent.resolve()
sys.path.append(str(TEST_ROOT.parent))


@pytest.fixture(scope="session")
def nixpkgs_path() -> str:
    """Session-scoped fixture that provides the nixpkgs store path."""
    project_root = TEST_ROOT.parent

    # Get the nixpkgs path using --inputs-from
    result = subprocess.run(
        nix_command(
            "flake",
            "metadata",
            "--json",
            "nixpkgs",
            "--inputs-from",
            str(project_root),
        ),
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    metadata = json.loads(result.stdout)
    try:
        return metadata["path"]
    except KeyError as e:
        msg = f"Failed to resolve nixpkgs path from flake metadata; got keys: {list(metadata.keys())}"
        raise RuntimeError(
            msg,
        ) from e


@pytest.fixture
def testpkgs(nixpkgs_path: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Fixture that provides a temporary directory with test packages."""
    with tempfile.TemporaryDirectory() as _tmpdirname:
        tmpdirname = Path(_tmpdirname)
        shutil.copytree(
            TEST_ROOT.joinpath("testpkgs"),
            tmpdirname,
            dirs_exist_ok=True,
        )

        # Patch the test flake.nix to use the main flake's nixpkgs
        flake_path = tmpdirname / "flake.nix"
        flake_content = flake_path.read_text()
        # Replace the placeholder with the actual nixpkgs path
        placeholder = 'nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";'
        patched_content = flake_content.replace(
            placeholder,
            f'nixpkgs.url = "path:{nixpkgs_path}";',
        )
        if patched_content == flake_content:
            msg = f"Failed to patch flake.nix; placeholder not found: {placeholder}"
            raise RuntimeError(
                msg,
            )
        flake_path.write_text(patched_content)

        # Set NIX_PATH for old Nix compatibility
        monkeypatch.setenv("NIX_PATH", f"nixpkgs={nixpkgs_path}")

        yield Path(tmpdirname)


@pytest.fixture
def testpkgs_git(testpkgs: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture that provides a temporary directory with test packages initialized as a git repo."""
    # Initialize git repo in the existing testpkgs directory
    monkeypatch.setenv("GIT_AUTHOR_NAME", "nix-update")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "nix-update@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "nix-update")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "nix-update@example.com")

    subprocess.run(["git", "-C", testpkgs, "init"], check=True)
    subprocess.run(["git", "-C", testpkgs, "add", "--all"], check=True)
    subprocess.run(
        ["git", "-C", testpkgs, "config", "commit.gpgsign", "false"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", testpkgs, "commit", "-m", "first commit"],
        check=True,
    )

    return testpkgs


class Helpers:
    @staticmethod
    def root() -> Path:
        return TEST_ROOT


@pytest.fixture  # type: ignore[misc]
def helpers() -> type[Helpers]:
    return Helpers
