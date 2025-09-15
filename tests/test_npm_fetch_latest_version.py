from __future__ import annotations

import io
import unittest.mock
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from nix_update.version import VersionFetchConfig, fetch_latest_version
from nix_update.version.version import VersionPreference

if TYPE_CHECKING:
    from tests import conftest


def fake_npm_urlopen(url: str, timeout: float | None = None) -> io.BytesIO:
    del timeout  # Unused in test
    if url == "https://registry.npmjs.org/@anthropic-ai/claude-code/latest":
        return io.BytesIO(b'{"version": "1.0.43"}')

    if url == "https://registry.npmjs.org/express/latest":
        return io.BytesIO(b'{"version": "4.21.2"}')

    raise ValueError(f"Unexpected URL in test: {url}")  # noqa: EM102, TRY003


def test_scoped_npm(helpers: conftest.Helpers) -> None:
    del helpers
    with unittest.mock.patch("urllib.request.urlopen", fake_npm_urlopen):
        assert (
            fetch_latest_version(
                urlparse(
                    "https://registry.npmjs.org/@anthropic-ai/claude-code/-/claude-code-1.0.42.tgz",
                ),
                VersionFetchConfig(
                    preference=VersionPreference.STABLE,
                    version_regex="(.*)",
                ),
            ).number
            == "1.0.43"
        )


def test_regular_npm(helpers: conftest.Helpers) -> None:
    del helpers
    with unittest.mock.patch("urllib.request.urlopen", fake_npm_urlopen):
        assert (
            fetch_latest_version(
                urlparse("https://registry.npmjs.org/express/-/express-4.21.1.tgz"),
                VersionFetchConfig(
                    preference=VersionPreference.STABLE,
                    version_regex="(.*)",
                ),
            ).number
            == "4.21.2"
        )
