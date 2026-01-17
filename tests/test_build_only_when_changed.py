"""Test that --build only runs when changes are detected."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


def test_build_skipped_when_no_changes(testpkgs_git: Path) -> None:
    """Test that nix_build is NOT called when version is already up to date."""
    with patch("nix_update.nix_build") as mock_build:
        # Use --version skip to skip version update entirely, so no changes occur
        # Use --commit to ensure proper git directory handling
        main(
            [
                "--file",
                str(testpkgs_git),
                "--build",
                "--commit",
                "--version",
                "skip",
                "github",
            ],
        )
        # Build should not be called since version didn't change
        mock_build.assert_not_called()

    # Verify no commit was made (only the initial commit exists)
    log = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "--oneline"],
        text=True,
        capture_output=True,
        check=True,
    )
    # Only the initial commit from testpkgs_git fixture
    assert len(log.stdout.strip().split("\n")) == 1


def test_build_runs_when_changes_detected(testpkgs_git: Path) -> None:
    """Test that nix_build IS called when version changes."""
    with patch("nix_update.nix_build") as mock_build:
        # Update to a newer version, so changes occur
        # Use --commit to ensure proper git directory handling
        main(
            [
                "--file",
                str(testpkgs_git),
                "--build",
                "--commit",
                "--version",
                "10.2.0",
                "github",
            ],
        )
        # Build should be called since version changed
        mock_build.assert_called_once()

    # Verify a commit was made
    log = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "--oneline"],
        text=True,
        capture_output=True,
        check=True,
    )
    # Initial commit + update commit
    expected_commit_count = 2
    assert len(log.stdout.strip().split("\n")) == expected_commit_count
