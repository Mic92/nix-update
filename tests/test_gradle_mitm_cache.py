import json
import subprocess
from pathlib import Path

from nix_update import main


def test_update(testpkgs_git: Path) -> None:
    main(
        [
            "--file",
            str(testpkgs_git),
            "--commit",
            "gradle-mitm-cache",
            "--version",
            "unstable",
        ],
    )

    deps_path = testpkgs_git / "gradle-mitm-cache" / "deps.json"
    with Path.open(deps_path) as f:
        deps = json.load(f)
        assert len(deps) > 0

    diff = subprocess.run(
        ["git", "-C", str(testpkgs_git), "show"],
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    print(diff)
    assert (
        "https://github.com/r00t0v3rr1d3/armitage/compare/c470e52773de4b44427ed4894c4096a44684b7e5..."
        in diff
    )
    assert "gradle-mitm-cache/deps.json" in diff
