import json
import re
from urllib.error import URLError
from urllib.parse import ParseResult
from urllib.request import urlopen

from .version import Version

KNOWN_GITEA_HOSTS = ["codeberg.org", "gitea.com", "akkoma.dev"]


def is_gitea_host(host: str) -> bool:
    if host in KNOWN_GITEA_HOSTS:
        return True
    endpoint = f"https://{host}/api/v1/signing-key.gpg"
    try:
        resp = urlopen(endpoint)
        return resp.status == 200
    except URLError:
        return False


def fetch_gitea_versions(url: ParseResult) -> list[Version]:
    if not is_gitea_host(url.netloc):
        return []

    _, owner, repo, *_ = url.path.split("/")
    repo = re.sub(r"\.git$", "", repo)
    tags_url = f"https://{url.netloc}/api/v1/repos/{owner}/{repo}/tags"
    resp = urlopen(tags_url)
    tags = json.loads(resp.read())
    return [Version(tag["name"]) for tag in tags]


def fetch_gitea_snapshots(url: ParseResult, branch: str) -> list[Version]:
    if not is_gitea_host(url.netloc):
        return []

    _, owner, repo, *_ = url.path.split("/")
    repo = re.sub(r"\.git$", "", repo)
    commits_url = f"https://{url.netloc}/api/v1/repos/{owner}/{repo}/commits?sha={branch}&limit=1&stat=false&verification=false&files=false"
    resp = urlopen(commits_url)
    commits = json.loads(resp.read())

    commit = next(iter(commits), None)
    if commit is None:
        return []

    versions = fetch_gitea_versions(url)
    latest_version = versions[0].number if versions else "0"

    date = commit["commit"]["committer"]["date"][:10]
    return [Version(f"{latest_version}-unstable-{date}", rev=commit["sha"])]
