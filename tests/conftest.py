from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from nix_update.utils import nix_command

if TYPE_CHECKING:
    from collections.abc import Iterator

TEST_ROOT = Path(__file__).parent.resolve()
sys.path.append(str(TEST_ROOT.parent))


@cache
def get_nixpkgs_path() -> str:
    """Get nixpkgs store path from the main flake, cached for the test session."""
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
        capture_output=True,
        text=True,
        check=True,
    )
    metadata = json.loads(result.stdout)
    return metadata["path"]


class Helpers:
    @staticmethod
    def root() -> Path:
        return TEST_ROOT

    @staticmethod
    @contextmanager
    def testpkgs(*, init_git: bool = False) -> Iterator[Path]:
        with tempfile.TemporaryDirectory() as _tmpdirname:
            tmpdirname = Path(_tmpdirname)
            shutil.copytree(
                Helpers.root().joinpath("testpkgs"),
                tmpdirname,
                dirs_exist_ok=True,
            )

            # Get the cached nixpkgs path and patch the test flake
            nixpkgs_path = get_nixpkgs_path()

            # Patch the test flake.nix to use the main flake's nixpkgs
            flake_path = tmpdirname / "flake.nix"
            flake_content = flake_path.read_text()
            # Replace the placeholder with the actual nixpkgs path
            patched_content = flake_content.replace(
                'nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";',
                f'nixpkgs.url = "path:{nixpkgs_path}";',
            )
            flake_path.write_text(patched_content)

            # Set NIX_PATH for old Nix compatibility
            os.environ["NIX_PATH"] = f"nixpkgs={nixpkgs_path}"

            if init_git:
                os.environ["GIT_AUTHOR_NAME"] = "nix-update"
                os.environ["GIT_AUTHOR_EMAIL"] = "nix-update@example.com"
                os.environ["GIT_COMMITTER_NAME"] = "nix-update"
                os.environ["GIT_COMMITTER_EMAIL"] = "nix-update@example.com"

                subprocess.run(["git", "-C", tmpdirname, "init"], check=True)
                subprocess.run(["git", "-C", tmpdirname, "add", "--all"], check=True)
                subprocess.run(
                    ["git", "-C", tmpdirname, "config", "commit.gpgsign", "false"],
                    check=True,
                )
                subprocess.run(
                    ["git", "-C", tmpdirname, "commit", "-m", "first commit"],
                    check=True,
                )
            yield Path(tmpdirname)


@pytest.fixture  # type: ignore[misc]
def helpers() -> type[Helpers]:
    return Helpers
