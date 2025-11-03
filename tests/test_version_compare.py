"""
Test suite for version_compare module.

These tests verify the version comparison algorithm handles various
version string formats correctly, including epochs, releases, and
mixed alphanumeric segments.
"""

import pytest

from nix_update.version_compare import version_compare


@pytest.mark.parametrize(
    ("ver1", "ver2", "expected"),
    [
        # Basic comparisons
        ("1.5.0", "1.5.0", 0),
        ("1.5.1", "1.5.0", 1),
        ("1.5.1", "1.5", 1),
        # With package release
        ("1.5.0-1", "1.5.0-1", 0),
        ("1.5.0-1", "1.5.0-2", -1),
        ("1.5.0-1", "1.5.1-1", -1),
        ("1.5.0-2", "1.5.1-1", -1),
        ("1.5-1", "1.5.1-1", -1),
        ("1.5-2", "1.5.1-1", -1),
        ("1.5-2", "1.5.1-2", -1),
        # Mixed package release inclusion
        ("1.5", "1.5-1", -1),
        ("1.1-1", "1.1", 1),
        ("1.0-1", "1.1", -1),
        ("1.1-1", "1.0", 1),
        # Alphanumeric versions
        ("1.5b-1", "1.5-1", -1),
        ("1.5b", "1.5", -1),
        ("1.5b-1", "1.5", -1),
        ("1.5b", "1.5.1", -1),
        # From the manpage
        ("1.0a", "1.0alpha", -1),
        ("1.0alpha", "1.0b", -1),
        ("1.0b", "1.0beta", -1),
        ("1.0beta", "1.0rc", -1),
        ("1.0rc", "1.0", -1),
        # Alpha-dotted versions
        ("1.5.a", "1.5", 1),
        ("1.5.b", "1.5.a", 1),
        ("1.5.1", "1.5.b", 1),
        # Alpha dots and dashes
        ("1.5.b-1", "1.5.b", 1),
        ("1.5-1", "1.5.b", -1),
        # Same/similar content, differing separators
        ("2.0", "2_0", 0),
        ("2.0_a", "2_0.a", 0),
        ("2.0a", "2.0.a", -1),
        ("2___a", "2_a", 1),
        # Epoch included version comparisons
        ("0:1.0", "0:1.0", 0),
        ("0:1.0", "0:1.1", -1),
        ("1:1.0", "0:1.0", 1),
        ("1:1.0", "0:1.1", 1),
        ("1:1.0", "2:1.1", -1),
        # Epoch + sometimes present pkgrel
        ("1:1.0", "0:1.0-1", 1),
        ("1:1.0-1", "0:1.1-1", 1),
        # Epoch included on one version
        ("0:1.0", "1.0", 0),
        ("0:1.0", "1.1", -1),
        ("0:1.1", "1.0", 1),
        ("1:1.0", "1.0", 1),
        ("1:1.0", "1.1", 1),
        ("1:1.1", "1.1", 1),
        # None handling
        (None, None, 0),
        (None, "1.0", -1),
        ("1.0", None, 1),
        # Real-world examples
        ("3.9.0", "3.10.0", -1),
        ("3.10.0", "3.9.0", 1),
        ("3.9.17", "3.9.18", -1),
        ("1.2.3", "1.2.4", -1),
        ("1.3.0", "1.2.9", 1),
        ("2.0.0", "1.99.99", 1),
        ("1.0.0rc1", "1.0.0rc2", -1),
        ("1.0.0rc2", "1.0.0", -1),
        ("1.0.0beta", "1.0.0rc", -1),
        ("1.0.0alpha", "1.0.0beta", -1),
        ("5.15.0", "5.16.0", -1),
        ("5.15.10", "5.15.9", 1),
        ("6.0.0", "5.19.0", 1),
        ("1.0.0.r5.gabcdef", "1.0.0.r6.gabcdef", -1),
        ("1.0.0.r10.gabcdef", "1.0.0.r9.gabcdef", 1),
    ],
)
def test_version_compare(ver1: str | None, ver2: str | None, expected: int) -> None:
    """Test version comparison returns expected result."""
    assert version_compare(ver1, ver2) == expected
    # Also test symmetry: version_compare(a, b) == -version_compare(b, a)
    if ver1 is not None and ver2 is not None:
        assert version_compare(ver2, ver1) == -expected
