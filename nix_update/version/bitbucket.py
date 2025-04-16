import json
from urllib.parse import ParseResult
from urllib.request import urlopen

from .version import Version


def fetch_bitbucket_versions(url: ParseResult, quiet: bool) -> list[Version]:
    if url.netloc not in ["bitbucket.org", "bitbucket.io"]:
        return []

    _, owner, repo, *_ = url.path.split("/")
    # paging controlled by pagelen parameter, by default it is 10
    tags_url = f"https://{url.netloc}/!api/2.0/repositories/{owner}/{repo}/refs/tags?sort=-target.date"
    resp = urlopen(tags_url)
    tags = json.loads(resp.read())["values"]
    return [Version(tag["name"]) for tag in tags]


def fetch_bitbucket_snapshots(
    url: ParseResult, branch: str, quiet: bool
) -> list[Version]:
    if url.netloc not in ["bitbucket.org", "bitbucket.io"]:
        return []

    _, owner, repo, *_ = url.path.split("/")
    # seems to ignore pagelen parameter (always returns one entry)
    commits_url = f'https://{url.netloc}/!api/2.0/repositories/{owner}/{repo}/refs?q=name="{branch}"'
    resp = urlopen(commits_url)
    ref = json.loads(resp.read())["values"][0]["target"]

    versions = fetch_bitbucket_versions(url, quiet)
    latest_version = versions[0].number if versions else "0"

    date = ref["date"][:10]  # to YYYY-MM-DD
    return [Version(f"{latest_version}-unstable-{date}", rev=ref["hash"])]
