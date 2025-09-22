"""Test hash extraction from Nix error messages."""

import pytest

from nix_update.dependency_hashes import extract_hash_from_nix_error


@pytest.mark.parametrize(
    ("stderr", "expected"),
    [
        # Hex hash
        (
            """
error: hash mismatch in fixed-output derivation:
         wanted: 0000000000000000000000000000000000000000000000000000000000000000
         got:    52d7a5f0bdabfd5a3fb2c8bb5eb26d3a3fb87653bc3a039c0dc09b849b3b9e75
    """,
            "52d7a5f0bdabfd5a3fb2c8bb5eb26d3a3fb87653bc3a039c0dc09b849b3b9e75",
        ),
        # SRI sha256 hash
        (
            """
error: hash mismatch in fixed-output derivation:
         specified: sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
            got:    sha256-kRMUuBeA8m/a+H4XF0IQvb1AyGusF5UhLyV83CNqHng=
    """,
            "sha256-kRMUuBeA8m/a+H4XF0IQvb1AyGusF5UhLyV83CNqHng=",
        ),
        # Real-world Nix error with multiple "got" lines
        (
            """
error: hash mismatch in fixed-output derivation '/nix/store/p0kp6w60lc31q67y4i3hn5mdkh0qkpzf-c680bec003e5f40175ef030a9b90c92cc2acc78a.patch.drv':
           likely URL: https://github.com/Mic92/nix-update/commit/c680bec003e5f40175ef030a9b90c92cc2acc78a.patch
            specified: sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
                  got: sha256-KUG4sPtk/igyava8LYMUjNx0HSuWH9ikGiAObULnAQ4=
        expected path: /nix/store/d0615dmx3mw6gvfd0pww6g57z1ib095f-c680bec003e5f40175ef030a9b90c92cc2acc78a.patch
             got path: /nix/store/wwg4kwld6k7721p5pnywvvr36bssgmji-c680bec003e5f40175ef030a9b90c92cc2acc78a.patch
    """,
            "sha256-KUG4sPtk/igyava8LYMUjNx0HSuWH9ikGiAObULnAQ4=",
        ),
        # Quoted hash
        (
            """
error: hash mismatch:
    expected '52d7a5f0bdabfd5a3fb2c8bb5eb26d3a3fb87653bc3a039c0dc09b849b3b9e75' but got 'abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
    """,
            "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        ),
        # SHA-512 SRI hash
        (
            """
error: hash mismatch:
         got:    sha512-vBnERTtz3BcVf1WrhYirX2pPPfHkIJjbtMcW8A7YoUG5HL0sIgLtfoccUlOPIxmPaNbJjuDoEhCTrwDJr2gZNKA==
    """,
            "sha512-vBnERTtz3BcVf1WrhYirX2pPPfHkIJjbtMcW8A7YoUG5HL0sIgLtfoccUlOPIxmPaNbJjuDoEhCTrwDJr2gZNKA==",
        ),
        # PNPM issue - last "got" hash should be extracted
        (
            """
Building pnpm...
got version 1.2.3
downloading got package...
error: hash mismatch:
         wanted: 0000000000000000000000000000000000000000000000000000000000000000
         got:    52d7a5f0bdabfd5a3fb2c8bb5eb26d3a3fb87653bc3a039c0dc09b849b3b9e75
    """,
            "52d7a5f0bdabfd5a3fb2c8bb5eb26d3a3fb87653bc3a039c0dc09b849b3b9e75",
        ),
        # MD5 hash
        (
            """
error: hash mismatch:
         got:    md5:5d41402abc4b2a76b9719d911017c592
    """,
            "md5:5d41402abc4b2a76b9719d911017c592",
        ),
        # SHA-1 SRI hash
        (
            """
error: hash mismatch:
         got:    sha1-aGVsbG8gd29ybGQ=
    """,
            "sha1-aGVsbG8gd29ybGQ=",
        ),
        # No hash found
        (
            """
error: some other error
no hash here
    """,
            None,
        ),
        # Empty stderr
        ("", None),
    ],
)
def test_extract_hash_from_nix_error(stderr: str, expected: str | None) -> None:
    """Test hash extraction from various Nix error formats."""
    result = extract_hash_from_nix_error(stderr)
    assert result == expected
