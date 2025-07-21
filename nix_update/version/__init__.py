import re
from collections.abc import Callable
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
from .version import Version, VersionPreference

# def find_repology_release(attr) -> str:
#    resp = urllib.request.urlopen(f"https://repology.org/api/v1/projects/{attr}/")
#    data = json.loads(resp.read())
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
    pattern = "rc|alpha|beta|preview|nightly|prerelease|m[0-9]+"
    return re.search(pattern, extracted, re.IGNORECASE) is not None


def fetch_latest_version(
    url: ParseResult,
    preference: VersionPreference,
    version_regex: str,
    branch: str | None = None,
    old_rev_tag: str | None = None,
    version_prefix: str = "",
    fetcher_args: dict[str, Any] | None = None,
) -> Version:
    unstable: list[str] = []
    filtered: list[str] = []
    used_fetchers = fetchers
    if preference == VersionPreference.BRANCH:
        assert branch is not None
        used_fetchers = [partial(f, branch=branch) for f in branch_snapshots_fetchers]

    used_fetchers = [
        (
            partial(cast("FetcherWithArgs", fetcher), extra_args=fetcher_args)
            if "extra_args" in signature(fetcher).parameters
            else fetcher
        )
        for fetcher in used_fetchers
    ]

    for fetcher in used_fetchers:
        versions = fetcher(url)
        if versions == []:
            continue
        final = []
        for version in versions:
            extracted = extract_version(version, version_regex)
            if extracted is None:
                filtered.append(version.number)
            elif preference == VersionPreference.STABLE and is_unstable(
                version,
                extracted.number,
            ):
                unstable.append(extracted.number)
            else:
                final.append(extracted)
        if final != []:
            if version_prefix != "":
                ver = next(
                    (
                        Version(
                            version.number.removeprefix(version_prefix),
                            prerelease=version.prerelease,
                            rev=version.rev or version.number,
                        )
                        for version in final
                        if version.number.startswith(version_prefix)
                    ),
                    None,
                )

                if ver is not None and ver.rev != old_rev_tag:
                    return ver

            return final[0]

    if filtered:
        raise VersionError(
            "No version matched the regex. The following versions were found:\n"
            + "\n".join(filtered),
        )

    if unstable:
        msg = f"Found an unstable version {unstable[0]}, which is being ignored. To update to unstable version, please use '--version=unstable'"
        raise VersionError(msg)

    msg = "Please specify the version. We can only get the latest version from codeberg/crates.io/gitea/github/gitlab/pypi/savannah/sourcehut/rubygems/npm projects right now"
    raise VersionError(msg)
