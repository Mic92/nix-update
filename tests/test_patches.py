import subprocess
from pathlib import Path

from nix_update import main
from nix_update.nix_ast import remove_list_elements


def drop(tmp_path: Path, expression: str, line: int, indices: set[int]) -> str:
    path = tmp_path / "package.nix"
    path.write_text(expression)
    remove_list_elements(str(path), "patches", line, indices)
    return path.read_text()


def test_remove_list_elements(tmp_path: Path) -> None:
    expression = """{
  # "patches = [" in a comment or string must not confuse us
  description = "patches = [ ./keep.patch ]";
  patches = [
    ./keep.patch # stays with keep.patch
    # merged upstream as ünïcode
    ./merged.patch
    (fetchpatch {
      url = "https://example.test/also-merged.patch?a=]";
      hash = "sha256-example";
    })
  ]
  ++ lib.optionals stdenv.isDarwin [ ./darwin.patch ];
}
"""
    assert (
        drop(tmp_path, expression, 4, {1, 2, 7})
        == """{
  # "patches = [" in a comment or string must not confuse us
  description = "patches = [ ./keep.patch ]";
  patches = [
    ./keep.patch # stays with keep.patch
  ]
  ++ lib.optionals stdenv.isDarwin [ ./darwin.patch ];
}
"""
    )


def test_remove_from_compact_list(tmp_path: Path) -> None:
    expression = "{ patches = [ ./merged.patch ./keep.patch ]; }\n"
    assert drop(tmp_path, expression, 1, {0}) == "{ patches = [  ./keep.patch ]; }\n"


def test_leaves_non_list_alone(tmp_path: Path) -> None:
    expression = "{ patches = lib.optionals true [ ./a.patch ]; }\n"
    assert drop(tmp_path, expression, 1, {0}) == expression


def test_drop_merged_patch_produced_by_derivation(testpkgs_git: Path) -> None:
    main(
        [
            "--file",
            str(testpkgs_git),
            "--version",
            "2",
            "--commit",
            "merged-patch",
        ],
    )

    diff = subprocess.run(
        ["git", "-C", testpkgs_git, "show", "--format=", "--", "merged-patch"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout
    assert '-  version = "1";' in diff
    assert '+  version = "2";' in diff
    updated = (testpkgs_git / "merged-patch" / "default.nix").read_text()
    assert '(runCommand "merged.patch"' not in updated
    assert '(runCommand "pending.patch"' in updated
