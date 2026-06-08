"""Test that subdirectory flakes are handled correctly.

Regression test for https://github.com/Mic92/nix-update/issues/534
When a flake lives in a subdirectory of a git repo (using ?dir=...),
nix flake metadata reports the git root as ``path`` but the flake.nix
lives in a subdirectory.  get_flake_store_path must append the dir
component so that builtins.getFlake can find the flake.nix.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from nix_update.options import get_flake_store_path

if TYPE_CHECKING:
    pass


def test_get_flake_store_path_appends_dir_for_subdir_flakes() -> None:
    """get_flake_store_path appends the dir query param from resolvedUrl."""
    fake_metadata = {
        "path": "/nix/store/abc123-source",
        "resolvedUrl": "git+file:///home/user/repo?dir=pkgs/my-flake",
    }
    fake_result = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=json.dumps(fake_metadata),
        stderr="",
    )
    with patch("subprocess.run", return_value=fake_result):
        result = get_flake_store_path("/home/user/repo/pkgs/my-flake")
    assert result == "/nix/store/abc123-source/pkgs/my-flake"


def test_get_flake_store_path_no_dir_param() -> None:
    """get_flake_store_path returns path as-is when there is no dir param."""
    fake_metadata = {
        "path": "/nix/store/abc123-source",
        "resolvedUrl": "git+file:///home/user/repo",
    }
    fake_result = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=json.dumps(fake_metadata),
        stderr="",
    )
    with patch("subprocess.run", return_value=fake_result):
        result = get_flake_store_path("/home/user/repo")
    assert result == "/nix/store/abc123-source"


def test_get_flake_store_path_no_resolved_url() -> None:
    """get_flake_store_path handles missing resolvedUrl gracefully."""
    fake_metadata = {
        "path": "/nix/store/abc123-source",
    }
    fake_result = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=json.dumps(fake_metadata),
        stderr="",
    )
    with patch("subprocess.run", return_value=fake_result):
        result = get_flake_store_path("/home/user/repo")
    assert result == "/nix/store/abc123-source"


@pytest.mark.skipif(
    shutil.which("nix") is None,
    reason="nix not available",
)
def test_get_flake_store_path_integration_subdir() -> None:
    """Integration test: a flake in a git subdirectory gets the correct store path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        subdir = root / "sub" / "flake"
        subdir.mkdir(parents=True)

        # Create a minimal flake in the subdirectory
        (subdir / "flake.nix").write_text(
            '{ outputs = { self }: { }; }\n'
        )

        # Initialize git repo at root
        subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(root), "add", "--all"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "config", "user.email", "test@test.com"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "config", "user.name", "test"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "config", "commit.gpgsign", "false"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "commit", "-m", "init"],
            check=True,
            capture_output=True,
        )

        result = get_flake_store_path(str(subdir))
        assert result is not None
        # The result should end with the subdirectory path
        assert result.endswith("/sub/flake"), f"Expected path ending with /sub/flake, got: {result}"
        # And should point to a valid nix store path
        assert result.startswith("/nix/store/")
        # And should contain a flake.nix
        assert Path(result, "flake.nix").exists()
