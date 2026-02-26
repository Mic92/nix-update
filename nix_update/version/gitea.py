from __future__ import annotations

import re
from datetime import datetime
from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib import request
from urllib.error import URLError

from .http import DEFAULT_TIMEOUT, fetch_json
from .version import Commit, Version

if TYPE_CHECKING:
    from urllib.parse import ParseResult
    from urllib.request import Request

KNOWN_GITEA_HOSTS = ["codeberg.org", "gitea.com", "akkoma.dev"]


# do not follow UI login redirects
class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *_args: object) -> Request | None:
        return None


OPENER = request.build_opener(NoRedirect)


def is_gitea_host(host: str) -> bool:
    if host in KNOWN_GITEA_HOSTS:
        return True
    endpoint = f"https://{host}/api/v1/settings/api"
    try:
        resp = OPENER.open(endpoint, timeout=DEFAULT_TIMEOUT)
    except URLError:
        return False
    else:
        return resp.status == HTTPStatus.OK


def fetch_gitea_versions(url: ParseResult) -> list[Version]:
    if not is_gitea_host(url.netloc):
        return []

    _, owner, repo, *_ = url.path.split("/")
    repo = re.sub(r"\.git$", "", repo)
    tags_url = f"https://{url.netloc}/api/v1/repos/{owner}/{repo}/tags"
    tags = fetch_json(tags_url)
    return [Version(tag["name"]) for tag in tags]


def fetch_gitea_snapshots(url: ParseResult, branch: str) -> list[Version]:
    if not is_gitea_host(url.netloc):
        return []

    _, owner, repo, *_ = url.path.split("/")
    repo = re.sub(r"\.git$", "", repo)
    commits_url = f"https://{url.netloc}/api/v1/repos/{owner}/{repo}/commits?sha={branch}&limit=1&stat=false&verification=false&files=false"
    commits = fetch_json(commits_url)

    commit = next(iter(commits), None)
    if commit is None:
        return []

    versions = fetch_gitea_versions(url)
    latest_version = versions[0].number if versions else "0"

    date = commit["commit"]["committer"]["date"]
    commit_date = datetime.fromisoformat(date)
    return [
        Version(
            f"{latest_version}-unstable-{date[:10]}",
            rev=commit["sha"],
            commit=Commit(sha=commit["sha"], date=commit_date),
        ),
    ]
