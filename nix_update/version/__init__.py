from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from inspect import signature
from typing import Any, Protocol, cast
from urllib.parse import ParseResult
from urllib.request import build_opener, install_opener

from nix_update.errors import VersionError
from nix_update.version_info import VERSION

from .bitbucket import fetch_bitbucket_snapshots, fetch_bitbucket_versions
from .crate import fetch_crate_versions
from .gitea import fetch_gitea_snapshots, fetch_gitea_versions
from .github import fetch_github_snapshots, fetch_github_versions
from .gitlab import fetch_gitlab_snapshots, fetch_gitlab_versions
from .npm import fetch_npm_versions
from .pypi import fetch_pypi_versions
from .rubygems import fetch_rubygem_versions
from .savannah import fetch_savannah_versions
from .sourcehut import fetch_sourcehut_snapshots, fetch_sourcehut_versions
from .sparkle import fetch_sparkle_versions
from .version import Version, VersionPreference


@dataclass
class VersionFetchConfig:
    preference: VersionPreference
    version_regex: str
    branch: str | None = None
    old_rev_tag: str | None = None
    version_prefix: str = ""
    fetcher_args: dict[str, Any] | None = field(default_factory=dict)


# def find_repology_release(attr) -> str:
#    data = fetch_json(f"https://repology.org/api/v1/projects/{attr}/")
#    for name, pkg in data.items():
#        for repo in pkg:
#            if repo["status"] == "newest":
#                return repo["version"]
#    return None

opener = build_opener()
opener.addheaders = [("User-Agent", f"nix-update/{VERSION}")]
install_opener(opener)


class SnapshotFetcher(Protocol):
    def __call__(self, url: ParseResult, branch: str) -> list[Version]: ...


class FetcherWithArgs(Protocol):
    def __call__(
        self,
        url: ParseResult,
        extra_args: dict[str, Any] | None = None,
    ) -> list[Version]: ...


Fetcher = Callable[[ParseResult], list[Version]] | FetcherWithArgs

fetchers: list[Fetcher] = [
    fetch_crate_versions,
    fetch_npm_versions,
    fetch_pypi_versions,
    fetch_github_versions,
    fetch_gitlab_versions,
    fetch_rubygem_versions,
    fetch_savannah_versions,
    fetch_sourcehut_versions,
    fetch_sparkle_versions,
    fetch_bitbucket_versions,
    # all entries below perform requests to check if the target url is of that type
    fetch_gitea_versions,
]

branch_snapshots_fetchers: list[SnapshotFetcher] = [
    fetch_github_snapshots,
    fetch_gitlab_snapshots,
    fetch_bitbucket_snapshots,
    fetch_sourcehut_snapshots,
    # all entries below perform requests to check if the target url is of that type
    fetch_gitea_snapshots,
]


def extract_version(version: Version, version_regex: str) -> Version | None:
    pattern = re.compile(version_regex)
    match = re.match(pattern, version.number)
    if match is not None:
        # Filter non-matched groups which come back as None.
        groups = [g for g in match.groups() if g]
        if len(groups) > 0:
            number = ".".join(groups)
            return Version(
                number,
                prerelease=version.prerelease,
                rev=version.rev
                or (None if version.number == number else version.number),
            )
    return None


def is_unstable(version: Version, extracted: str) -> bool:
    if version.prerelease is not None:
        return version.prerelease
    pattern = "alpha|beta|canary|m[0-9]+|nightly|prerelease|preview|rc"
    return re.search(pattern, extracted, re.IGNORECASE) is not None


def prepare_fetchers(config: VersionFetchConfig) -> list:
    used_fetchers = fetchers
    if config.preference == VersionPreference.BRANCH:
        if config.branch is None:
            msg = "Branch must be specified when using BRANCH preference"
            raise ValueError(msg)
        used_fetchers = [
            partial(f, branch=config.branch) for f in branch_snapshots_fetchers
        ]

    return [
        (
            partial(cast("FetcherWithArgs", fetcher), extra_args=config.fetcher_args)
            if "extra_args" in signature(fetcher).parameters
            else fetcher
        )
        for fetcher in used_fetchers
    ]


def find_prefixed_version(
    final_versions: list,
    config: VersionFetchConfig,
) -> Version | None:
    if config.version_prefix == "":
        return None

    ver = next(
        (
            Version(
                version.number.removeprefix(config.version_prefix),
                prerelease=version.prerelease,
                rev=version.rev or version.number,
            )
            for version in final_versions
            if version.number.startswith(config.version_prefix)
        ),
        None,
    )

    if ver is not None and ver.rev != config.old_rev_tag:
        return ver
    return None


def fetch_latest_version(
    url: ParseResult,
    config: VersionFetchConfig,
) -> Version:
    used_fetchers = prepare_fetchers(config)
    all_unstable: list[str] = []
    all_filtered: list[str] = []

    for fetcher in used_fetchers:
        versions = fetcher(url)
        if not versions:
            continue

        final = []
        unstable = []
        filtered = []

        for version in versions:
            extracted = extract_version(version, config.version_regex)
            if extracted is None:
                filtered.append(version.number)
            elif config.preference == VersionPreference.STABLE and is_unstable(
                version,
                extracted.number,
            ):
                unstable.append(extracted.number)
            else:
                final.append(extracted)
        all_unstable.extend(unstable)
        all_filtered.extend(filtered)

        if final:
            prefixed_version = find_prefixed_version(final, config)
            if prefixed_version is not None:
                return prefixed_version
            return final[0]

    if all_filtered:
        raise VersionError(
            "No version matched the regex. The following versions were found:\n"
            + "\n".join(all_filtered),
        )

    if all_unstable:
        msg = f"Found an unstable version {all_unstable[0]}, which is being ignored. To update to unstable version, please use '--version=unstable'"
        raise VersionError(msg)

    msg = "Please specify the version. We can only get the latest version from codeberg/crates.io/gitea/github/gitlab/pypi/savannah/sourcehut/rubygems/npm projects right now"
    raise VersionError(msg)
