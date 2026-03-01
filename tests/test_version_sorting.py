"""
Test that fetch_latest_version picks the highest semver version,
not the most recently published one.

This covers the scenario where upstream maintains multiple release
branches and publishes patch releases for older branches after newer
minor/major versions exist (e.g. openshift-pipelines/pipelines-as-code
publishes v0.39.5 after v0.41.1).
"""

from __future__ import annotations

import io
import typing
import unittest.mock
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

if typing.TYPE_CHECKING:
    from urllib.request import Request

from nix_update.version import VersionFetchConfig, fetch_latest_version
from nix_update.version.version import VersionPreference


def _build_github_atom_feed(releases: list[str]) -> bytes:
    """Build a minimal GitHub-style Atom feed with entries in the given order."""
    ns = "http://www.w3.org/2005/Atom"
    feed = ET.Element(f"{{{ns}}}feed")
    ET.SubElement(feed, f"{{{ns}}}title").text = "Release feed"
    for tag in releases:
        entry = ET.SubElement(feed, f"{{{ns}}}entry")
        link = ET.SubElement(entry, f"{{{ns}}}link")
        link.set("href", f"https://github.com/owner/repo/releases/tag/{tag}")
        ET.SubElement(entry, f"{{{ns}}}updated").text = "2026-01-01T00:00:00Z"
    return ET.tostring(feed, encoding="unicode").encode()


class _FakeUrlopen:
    """Callable that replaces ``urllib.request.urlopen`` in tests."""

    def __init__(self, feed_bytes: bytes) -> None:
        self.feed_bytes = feed_bytes

    def __call__(
        self,
        request: str | Request,
        timeout: int | None = None,
    ) -> io.BytesIO:
        _ = request, timeout  # satisfy interface contract
        resp = io.BytesIO(self.feed_bytes)
        resp.status = 200  # type: ignore[attr-defined]
        return resp


def test_highest_semver_wins_over_recent_release() -> None:
    """Simulate the tektoncd-cli-pac scenario: v0.39.5 released after v0.41.1."""
    # Feed ordered by release date (most recent first) — v0.39.5 is newest
    feed = _build_github_atom_feed(
        ["v0.39.5", "v0.37.6", "v0.41.1", "v0.39.4", "v0.37.5", "v0.41.0"],
    )
    with unittest.mock.patch(
        "nix_update.version.github.urllib.request.urlopen",
        _FakeUrlopen(feed),
    ):
        version = fetch_latest_version(
            urlparse(
                "https://github.com/openshift-pipelines/pipelines-as-code/archive/v0.41.1.tar.gz",
            ),
            VersionFetchConfig(
                preference=VersionPreference.STABLE,
                version_regex=r"v([0-9.]+)",
            ),
        )
        assert version.number == "0.41.1"


def test_highest_semver_without_version_regex() -> None:
    """Even without --version-regex, the highest version should be selected."""
    feed = _build_github_atom_feed(
        ["v0.39.5", "v0.41.1", "v0.37.6"],
    )
    with unittest.mock.patch(
        "nix_update.version.github.urllib.request.urlopen",
        _FakeUrlopen(feed),
    ):
        version = fetch_latest_version(
            urlparse(
                "https://github.com/owner/repo/archive/v0.41.1.tar.gz",
            ),
            VersionFetchConfig(
                preference=VersionPreference.STABLE,
                version_regex=r"(.*)",
            ),
        )
        assert version.number == "v0.41.1"


def test_sorting_with_major_version_differences() -> None:
    """Ensure major version bumps are preferred over older branch patches."""
    feed = _build_github_atom_feed(
        ["v1.2.10", "v2.0.0", "v1.3.0", "v1.2.9"],
    )
    with unittest.mock.patch(
        "nix_update.version.github.urllib.request.urlopen",
        _FakeUrlopen(feed),
    ):
        version = fetch_latest_version(
            urlparse(
                "https://github.com/owner/repo/archive/v2.0.0.tar.gz",
            ),
            VersionFetchConfig(
                preference=VersionPreference.STABLE,
                version_regex=r"v([0-9.]+)",
            ),
        )
        assert version.number == "2.0.0"


def test_postgis_scenario() -> None:
    """PostGIS: 3.5.4 published after 3.6.0 — should pick 3.6.0."""
    feed = _build_github_atom_feed(
        ["3.5.4", "3.6.0", "3.5.3", "3.4.5"],
    )
    with unittest.mock.patch(
        "nix_update.version.github.urllib.request.urlopen",
        _FakeUrlopen(feed),
    ):
        version = fetch_latest_version(
            urlparse(
                "https://github.com/postgis/postgis/archive/3.6.0.tar.gz",
            ),
            VersionFetchConfig(
                preference=VersionPreference.STABLE,
                version_regex=r"([0-9.]+)",
            ),
        )
        assert version.number == "3.6.0"
