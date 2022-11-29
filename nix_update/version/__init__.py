import re
from functools import partial
from typing import Callable, List, Optional
from urllib.parse import ParseResult

from ..errors import VersionError
from .crate import fetch_crate_versions
from .github import fetch_github_snapshots, fetch_github_versions
from .gitlab import fetch_gitlab_snapshots, fetch_gitlab_versions
from .pypi import fetch_pypi_versions
from .rubygems import fetch_rubygem_versions
from .savannah import fetch_savannah_versions
from .sourcehut import fetch_sourcehut_versions
from .version import Version, VersionPreference

# def find_repology_release(attr) -> str:
#    resp = urllib.request.urlopen(f"https://repology.org/api/v1/projects/{attr}/")
#    data = json.loads(resp.read())
#    for name, pkg in data.items():
#        for repo in pkg:
#            if repo["status"] == "newest":
#                return repo["version"]
#    return None

fetchers: List[Callable[[ParseResult], List[Version]]] = [
    fetch_crate_versions,
    fetch_pypi_versions,
    fetch_github_versions,
    fetch_gitlab_versions,
    fetch_rubygem_versions,
    fetch_savannah_versions,
    fetch_sourcehut_versions,
]

branch_snapshots_fetchers: List[Callable[[ParseResult, str], List[Version]]] = [
    fetch_github_snapshots,
    fetch_gitlab_snapshots,
]


def extract_version(version: Version, version_regex: str) -> Optional[Version]:
    pattern = re.compile(version_regex)
    match = re.match(pattern, version.number)
    if match is not None:
        group = match.group(1)
        if group is not None:
            return Version(
                group,
                prerelease=version.prerelease,
                rev=version.rev
                or (None if version.number == group else version.number),
            )
    return None


def is_unstable(version: Version, extracted: str) -> bool:
    if version.prerelease is not None:
        return version.prerelease
    pattern = "rc|alpha|beta|preview|nightly|m[0-9]+"
    return re.search(pattern, extracted, re.IGNORECASE) is not None


def fetch_latest_version(
    url: ParseResult,
    preference: VersionPreference,
    version_regex: str,
    branch: Optional[str] = None,
    old_rev: Optional[str] = None,
    version_prefix: str = "",
) -> Version:
    unstable: List[str] = []
    filtered: List[str] = []
    used_fetchers = fetchers
    if preference == VersionPreference.BRANCH:
        used_fetchers = [partial(f, branch=branch) for f in branch_snapshots_fetchers]
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
                version, extracted.number
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

                if ver is not None and ver.rev != old_rev:
                    return ver

            return final[0]

    if filtered:
        raise VersionError(
            "Not version matched the regex. The following versions were found:\n"
            + "\n".join(filtered)
        )

    if unstable:
        raise VersionError(
            f"Found an unstable version {unstable[0]}, which is being ignored. To update to unstable version, please use '--version=unstable'"
        )

    raise VersionError(
        "Please specify the version. We can only get the latest version from github/gitlab/pypi/rubygems projects right now"
    )
