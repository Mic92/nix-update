"""Test that --build only runs when changes are detected."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


def test_build_skipped_when_no_changes(testpkgs_git: Path) -> None:
    """Test that nix_build is NOT called when the package is already up to date."""
    # Bring the package up to date first.
    main(["--file", str(testpkgs_git), "--commit", "--version", "10.2.0", "github"])

    with patch("nix_update.nix_build") as mock_build:
        # Second run skips the version update and re-computes the same hash,
        # so no changes are produced.
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
        mock_build.assert_not_called()

    # Only the initial commit and the first update commit exist.
    log = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "--oneline"],
        text=True,
        capture_output=True,
        check=True,
    )
    expected_commit_count = 2
    assert len(log.stdout.strip().split("\n")) == expected_commit_count


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
