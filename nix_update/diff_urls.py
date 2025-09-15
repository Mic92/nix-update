"""Module for generating diff URLs for various package repositories."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .errors import UpdateError
from .eval import Package, eval_attr

if TYPE_CHECKING:
    from .options import Options
    from .version.version import Version

GITLAB_API = re.compile(r"https://(gitlab.com|([^/]+)/api/v4)/")


def create_crates_diff_url(package: Package, new_version: Version) -> str:
    crates_path_min_parts = 5

    if package.parsed_url is None:
        msg = "Package parsed_url is None"
        raise UpdateError(msg)
    parts = package.parsed_url.path.split("/")
    if len(parts) < crates_path_min_parts:
        msg = f"Unexpected crates.io URL path structure: {package.parsed_url.path}"
        raise UpdateError(msg)
    return f"https://diff.rs/{parts[crates_path_min_parts - 1]}/{package.old_version}/{new_version.number}"


def create_npm_diff_url(package: Package, new_version: Version) -> str:
    npm_path_min_parts = 2
    npm_scoped_path_min_parts = 3
    npm_package_index = 1
    npm_scoped_name_index = 2

    if package.parsed_url is None:
        msg = "Package parsed_url is None"
        raise UpdateError(msg)
    parts = package.parsed_url.path.split("/")
    if len(parts) < npm_path_min_parts:
        msg = f"Unexpected npm URL path structure: {package.parsed_url.path}"
        raise UpdateError(msg)
    if parts[npm_package_index].startswith("@"):
        if len(parts) < npm_scoped_path_min_parts:
            msg = f"Unexpected scoped npm package URL structure: {package.parsed_url.path}"
            raise UpdateError(msg)
        package_name = f"{parts[npm_package_index]}%2F{parts[npm_scoped_name_index]}"
    else:
        package_name = parts[npm_package_index]
    return (
        f"https://npmdiff.dev/{package_name}/{package.old_version}/{new_version.number}"
    )


def extract_github_rev_tag(url_path: str) -> str | None:
    regex = re.compile(".*/releases/download/(.*)/.*")
    match = regex.match(url_path)
    return match.group(1) if match else None


def create_github_diff_url(
    opts: Options,
    package: Package,
    new_version: Version,
) -> str | None:
    if package.parsed_url is None:
        return None
    _, owner, repo, *_ = package.parsed_url.path.split("/")
    old_rev_tag = package.tag or package.rev

    if old_rev_tag is None:
        old_rev_tag = extract_github_rev_tag(package.parsed_url.path)

    new_rev_tag = new_version.tag or new_version.rev
    if new_rev_tag is None:
        new_package = eval_attr(opts)
        new_rev_tag = new_package.tag or new_package.rev

        if new_rev_tag is None and new_package.parsed_url is not None:
            new_rev_tag = extract_github_rev_tag(new_package.parsed_url.path)

    if old_rev_tag is not None and new_rev_tag is not None:
        return f"https://github.com/{owner}/{repo.removesuffix('.git')}/compare/{old_rev_tag}...{new_rev_tag}"
    return None


def create_other_diff_urls(package: Package, new_version: Version) -> str | None:
    if package.parsed_url is None:
        return None
    old_rev_tag = package.tag or package.rev
    netloc = package.parsed_url.netloc

    if netloc in ["codeberg.org", "gitea.com"]:
        _, owner, repo, *_ = package.parsed_url.path.split("/")
        return f"https://{netloc}/{owner}/{repo}/compare/{old_rev_tag}...{new_version.rev or new_version.number}"
    if GITLAB_API.match(package.parsed_url.geturl()) and package.src_homepage:
        return f"{package.src_homepage}-/compare/{old_rev_tag}...{new_version.rev or new_version.number}"
    if netloc in ["bitbucket.org", "bitbucket.io"]:
        _, owner, repo, *_ = package.parsed_url.path.split("/")
        return f"https://{netloc}/{owner}/{repo}/branches/compare/{new_version.rev or new_version.number}%0D{old_rev_tag}"
    return None


def generate_diff_url(opts: Options, package: Package, new_version: Version) -> None:
    if not package.parsed_url:
        return

    netloc = package.parsed_url.netloc
    diff_url = None

    if netloc == "crates.io":
        diff_url = create_crates_diff_url(package, new_version)
    elif netloc == "registry.npmjs.org":
        diff_url = create_npm_diff_url(package, new_version)
    elif netloc == "github.com":
        diff_url = create_github_diff_url(opts, package, new_version)
    else:
        diff_url = create_other_diff_urls(package, new_version)

    if diff_url:
        package.diff_url = diff_url
