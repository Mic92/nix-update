import subprocess
from pathlib import Path

import pytest

from nix_update import main
from nix_update.nix_ast import remove_list_elements


def drop(
    tmp_path: Path,
    expression: str,
    line: int,
    indices: set[int],
    total: int | None = None,
) -> str:
    path = tmp_path / "package.nix"
    path.write_text(expression)
    total = expression.count(".patch") if total is None else total
    remove_list_elements(str(path), "patches", line, indices, total)
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
        drop(tmp_path, expression, 4, {1, 2, 7}, total=4)
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


def test_comments_follow_their_element(tmp_path: Path) -> None:
    expression = """{
  patches = [
    # section

    # about a
    # more about a
    ./a.patch # trailing a
    # about b
    ./b.patch
  ];
}
"""
    assert (
        drop(tmp_path, expression, 2, {0})
        == """{
  patches = [
    # section

    # about b
    ./b.patch
  ];
}
"""
    )


@pytest.mark.parametrize(
    ("expression", "line", "total"),
    [
        # not a list
        ("{ patches = lib.optionals true [ ./a.patch ]; }\n", 1, 1),
        # a wrapper added patches, so indices do not match the source
        ("{ patches = [ ./a.patch ]; }\n", 1, 2),
        # reported in another file, this list merely has the same name
        ("{\n  foo = 1;\n  other.patches = [ ./a.patch ];\n}\n", 2, 1),
        ("{\n  foo = 1;\n  patches = [ ./a.patch ] ++ more;\n}\n", 2, 2),
    ],
)
def test_leaves_unexpected_lists_alone(
    tmp_path: Path, expression: str, line: int, total: int
) -> None:
    assert drop(tmp_path, expression, line, {0}, total) == expression


def test_follows_inherit(tmp_path: Path) -> None:
    expression = "let patches = [ ./a.patch ]; in { inherit patches; }\n"
    assert drop(tmp_path, expression, 1, {0}) == expression.replace("./a.patch", "")


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
