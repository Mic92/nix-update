import json
from urllib.parse import ParseResult
from urllib.request import urlopen

from .version import Version


def fetch_gitea_versions(url: ParseResult) -> list[Version]:
    if url.netloc not in ["codeberg.org", "gitea.com", "notabug.org"]:
        return []

    _, owner, repo, *_ = url.path.split("/")
    tags_url = f"https://{url.netloc}/api/v1/repos/{owner}/{repo}/tags"
    resp = urlopen(tags_url)
    tags = json.loads(resp.read())
    return [Version(tag["name"]) for tag in tags]


def fetch_gitea_snapshots(url: ParseResult, branch: str) -> list[Version]:
    if url.netloc not in ["codeberg.org", "gitea.com", "notabug.org"]:
        return []

    _, owner, repo, *_ = url.path.split("/")
    commits_url = f"https://{url.netloc}/api/v1/repos/{owner}/{repo}/commits?sha={branch}&limit=1stat=false"
    resp = urlopen(commits_url)
    commits = json.loads(resp.read())

    commit = next(iter(commits), None)
    if commit is None:
        return []

    versions = fetch_gitea_versions(url)
    latest_version = versions[0].number if versions else "0"

    date = commit["commit"]["committer"]["date"][:10]
    return [Version(f"{latest_version}-unstable-{date}", rev=commit["sha"])]
