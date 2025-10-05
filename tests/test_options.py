from __future__ import annotations

import pytest

from nix_update.errors import AttributePathError
from nix_update.options import parse_attribute_path


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
