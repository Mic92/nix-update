from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

from nix_update import main

if TYPE_CHECKING:
    from pathlib import Path


def test_main(testpkgs_git: Path) -> None:
    main(["--file", str(testpkgs_git), "--commit", "version-prefix"])
    version = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--extra-experimental-features",
            "nix-command",
            "-f",
            testpkgs_git,
            "version-prefix.version",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    # upstream tags may have non-numeric suffixes like "0.9.140-b.1"
    numeric_version = tuple(
        int(match.group())
        for part in version.split(".")
        if (match := re.match(r"\d+", part))
    )
    assert numeric_version >= (0, 9, 0)
    commit = subprocess.run(
        ["git", "-C", str(testpkgs_git), "log", "-1"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(commit)
    assert version in commit
    assert "version-prefix" in commit
    assert (
        "https://github.com/nextest-rs/nextest/compare/cargo-nextest-0.9.0...cargo-nextest-"
        in commit
    )
