"""Hash utility functions for nix-update."""

from subprocess import run as subprocess_run

# Hash length constants for SRI format conversion
MD5_HASH_LENGTH = 32
SHA1_HASH_LENGTH = 40


def to_sri(hashstr: str) -> str:
    """Convert a hash string to SRI format if needed."""
    if "-" in hashstr:
        return hashstr
    length = len(hashstr)
    if length == MD5_HASH_LENGTH:
        prefix = "md5:"
    elif length == SHA1_HASH_LENGTH:
        prefix = "sha1:"
    else:
        prefix = "sha256:"

    cmd = ["nix", "--extra-experimental-features", "nix-command", "hash", "to-sri"]

    res = subprocess_run(
        [*cmd, f"{prefix}{hashstr}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.rstrip()
