from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from nix_update.errors import AttributePathError
from nix_update.options import get_flake_store_path, parse_attribute_path


@pytest.mark.parametrize(
    ("input_attr", "expected_parts"),
    [
        # Simple cases
        ("foo", ["foo"]),
        ("foo.bar", ["foo", "bar"]),
        ("foo.bar.baz", ["foo", "bar", "baz"]),
        # Quoted components with dots
        ('foo."bar.baz"', ["foo", "bar.baz"]),
        ('"foo.bar".baz', ["foo.bar", "baz"]),
        ('"foo.bar"."baz.qux"', ["foo.bar", "baz.qux"]),
        # Real-world examples
        ("cargoLock.update", ["cargoLock", "update"]),
        ("passthru.tests.basic", ["passthru", "tests", "basic"]),
        # Quoted empty string
        ('""', [""]),
        ('foo.""', ["foo", ""]),
        # Escaped quotes within quoted strings
        ('foo."bar\\"baz"', ["foo", 'bar"baz']),
        ('"foo\\"bar"', ['foo"bar']),
        ('packages.\\"x86_64-linux\\"', ["packages", "x86_64-linux"]),
    ],
)
def test_parse_attribute_path(input_attr: str, expected_parts: list[str]) -> None:
    """Test parsing of attribute paths with various formats."""
    assert parse_attribute_path(input_attr) == expected_parts


@pytest.mark.parametrize(
    ("input_attr", "error_match"),
    [
        # Empty string
        ("", "Attribute path cannot be empty"),
        # Leading dot
        (".foo", "leading dot"),
        # Trailing dot
        ("foo.", "trailing dot"),
        # Consecutive dots
        ("foo..bar", "consecutive dots"),
        # Unclosed quotes
        ('foo."bar', "unclosed quote"),
        ('"foo', "unclosed quote"),
        # Trailing backslash
        ("foo\\", "trailing escape"),
        ('foo."bar\\', "trailing escape"),
    ],
)
def test_parse_attribute_path_errors(input_attr: str, error_match: str) -> None:
    """Test that invalid attribute paths raise AttributePathError."""
    with pytest.raises(AttributePathError, match=error_match):
        parse_attribute_path(input_attr)


def test_get_flake_store_path_subdir(tmp_path: Path) -> None:
    """Flakes in a git subdirectory resolve to the subdirectory store path."""
    subdir = tmp_path / "systems" / "nixos"
    subdir.mkdir(parents=True)
    (subdir / "flake.nix").write_text("{ outputs = _: { }; }")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)

    store_path = get_flake_store_path(str(subdir))

    assert store_path is not None
    assert store_path.endswith("/systems/nixos")
    assert (Path(store_path) / "flake.nix").exists()


def test_get_flake_store_path_lazy_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A store path that metadata did not materialize is prefetched."""
    (tmp_path / "flake.nix").write_text("{ outputs = _: { }; }")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)

    virtual_path = "/nix/store/00000000000000000000000000000000-lazy-source"
    real_run = subprocess.run

    def lazy_metadata_run(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        if list(args[0][:3]) == ["nix", "flake", "metadata"]:
            metadata = {"path": virtual_path}
            return subprocess.CompletedProcess(
                args=args[0],
                returncode=0,
                stdout=json.dumps(metadata),
                stderr="",
            )
        return real_run(*args, **kwargs)

    monkeypatch.setattr("nix_update.options.subprocess.run", lazy_metadata_run)

    store_path = get_flake_store_path(str(tmp_path))

    assert store_path is not None
    assert store_path != virtual_path
    assert (Path(store_path) / "flake.nix").exists()
