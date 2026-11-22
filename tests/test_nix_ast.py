from __future__ import annotations

from nix_update.cargo import set_output_hashes
from nix_update.nix_ast import replace_in_strings

PACKAGE = """{
  # was "1.0" before abc123
  version = "1.0";
  src = fetchurl {
    url = "https://example.test/${pname}-abc123.tar.gz";
    rev = "abc123";
  };
  passthru.compat = "1.0";
  abc123 = true;
}
"""


def test_replace_in_strings() -> None:
    # everything but the identifier
    assert replace_in_strings(PACKAGE, "abc123", "def456") == PACKAGE.replace(
        "abc123", "def456"
    ).replace("def456 = true", "abc123 = true")


def test_replace_whole_strings() -> None:
    updated = replace_in_strings(PACKAGE, "1.0", "2.0", whole=True)
    assert updated == PACKAGE.replace('= "1.0"', '= "2.0"')
    updated = replace_in_strings(PACKAGE, "1.0", "2.0", whole=True, line=3)
    assert updated == PACKAGE.replace('version = "1.0"', 'version = "2.0"')


def test_replace_in_other_formats() -> None:
    text = '{"version": "1.0", "rev": "abc123"}\n'
    assert replace_in_strings(text, "abc123", "def456") == text.replace(
        "abc123", "def456"
    )
    assert replace_in_strings(text, "1.0", "2.0", whole=True) == text.replace(
        "1.0", "2.0"
    )


def test_set_output_hashes_short() -> None:
    text = """{
  cargoLock.lockFile = ./Cargo.lock;
  cargoLock.outputHashes."old-1.0" = "sha256-old";
  doCheck = false;
}
"""
    assert (
        set_output_hashes(text, {"new-2.0": "sha256-new"})
        == """{
  cargoLock.lockFile = ./Cargo.lock;
  cargoLock.outputHashes = {
    "new-2.0" = "sha256-new";
  };
  doCheck = false;
}
"""
    )


def test_set_output_hashes_expanded() -> None:
    text = """{
  cargoLock = {
    lockFile = ./Cargo.lock;
    # forks
    outputHashes = {
      "old-1.0" = "sha256-old";
    };
    allowBuiltinFetchGit = false;
  };
}
"""
    replaced = text.replace("old-1.0", "new-2.0").replace("sha256-old", "sha256-new")
    assert set_output_hashes(text, {"new-2.0": "sha256-new"}) == replaced
    removed = set_output_hashes(text, {})
    assert "outputHashes" not in removed
    assert (
        set_output_hashes(removed, {"old-1.0": "sha256-old"})
        == """{
  cargoLock = {
    lockFile = ./Cargo.lock;
    outputHashes = {
      "old-1.0" = "sha256-old";
    };
    # forks
    allowBuiltinFetchGit = false;
  };
}
"""
    )


def test_set_output_hashes_picks_the_cargo_lock_file() -> None:
    text = """{
  npmDeps = importNpmLock { lockFile = ./package-lock.json; };
  cargoDeps = rustPlatform.importCargoLock { lockFile = ./Cargo.lock; };
}
"""
    assert (
        set_output_hashes(text, {"new-2.0": "sha256-new"})
        == """{
  npmDeps = importNpmLock { lockFile = ./package-lock.json; };
  cargoDeps = rustPlatform.importCargoLock { lockFile = ./Cargo.lock;
    outputHashes = {
      "new-2.0" = "sha256-new";
    }; };
}
"""
    )
