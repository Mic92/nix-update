from __future__ import annotations

import io
import json
import unittest.mock
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

from nix_update.version import VersionFetchConfig, fetch_latest_version
from nix_update.version.version import VersionPreference

if TYPE_CHECKING:
    from urllib.request import Request

TARBALL_URL = (
    "https://gitlab.com/api/v4/projects/42/repository/archive.tar.gz?sha=v1.0.0"
)
TAGS_URL = "https://gitlab.com/api/v4/projects/42/repository/tags"

TAGS_RESPONSE = json.dumps([{"name": "v1.1.0"}, {"name": "v1.0.0"}]).encode()


@pytest.mark.parametrize(
    ("env", "expected_auth"),
    [
        ({}, None),
        ({"GITLAB_TOKEN": "secret123"}, "Bearer secret123"),
    ],
)
def test_gitlab_token(env: dict[str, str], expected_auth: str | None) -> None:
    seen_headers: dict[str, str] = {}

    def fake_urlopen(request: Request, timeout: float | None = None) -> io.BytesIO:
        del timeout  # Unused in test
        seen_headers.update(request.headers)
        assert request.full_url == TAGS_URL
        return io.BytesIO(TAGS_RESPONSE)

    with (
        unittest.mock.patch("nix_update.version.http.urlopen", fake_urlopen),
        unittest.mock.patch.dict("os.environ", env, clear=True),
    ):
        version = fetch_latest_version(
            urlparse(TARBALL_URL),
            VersionFetchConfig(
                preference=VersionPreference.STABLE,
                version_regex="(.*)",
            ),
        )
    assert version.number == "v1.1.0"
    assert seen_headers.get("Authorization") == expected_auth
