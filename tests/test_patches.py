import subprocess
from pathlib import Path

from nix_update import main
from nix_update.patches import drop_patch_indices


def test_drop_local_and_fetchpatch_expressions(tmp_path: Path) -> None:
    expression = tmp_path / "package.nix"
    expression.write_text(
        """patches = [
  ./keep.patch
  ./merged.patch
  (fetchpatch {
    url = "https://example.test/also-merged.patch";
    hash = "sha256-example";
  })
];
""",
    )

    drop_patch_indices(str(expression), 1, {1, 2})

    assert (
        expression.read_text()
        == """patches = [
  ./keep.patch
];
"""
    )


def test_arbitrary_patch_expression_is_removed_by_index(tmp_path: Path) -> None:
    expression = tmp_path / "package.nix"
    original = """patches = [
  ./fix.patch
  (fetchpatch { url = "https://example.test/fix.patch"; })
];
"""
    expression.write_text(original)

    drop_patch_indices(str(expression), 1, {1})

    assert (
        expression.read_text()
        == """patches = [
  ./fix.patch
];
"""
    )


def test_compact_patch_list_entry_is_removed(tmp_path: Path) -> None:
    expression = tmp_path / "package.nix"
    original = "patches = [ ./merged.patch ];\n"
    expression.write_text(original)

    drop_patch_indices(str(expression), 1, {0})

    assert expression.read_text() == "patches = [  ];\n"


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
