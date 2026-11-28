from __future__ import annotations

import re
from datetime import UTC, datetime
from functools import cache
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode, urlparse

from nix_update.errors import VersionError
from nix_update.utils import info

from .http import fetch_json
from .version import Version

if TYPE_CHECKING:
    from urllib.parse import ParseResult

TANGLED_DID = re.compile(r"/(did:[a-z]+:[^/]+)")


def tangled_did(url: ParseResult) -> str | None:
    match = TANGLED_DID.match(url.path)
    return match.group(1) if match else None


@cache
def knot_url(did: str) -> str:
    if not did.startswith("did:plc:"):
        msg = f"Only did:plc tangled repositories are supported, got {did}"
        raise VersionError(msg)
    doc_url = f"https://plc.directory/{did}"
    info(f"fetch {doc_url}")
    services = {
        s["id"]: s["serviceEndpoint"] for s in fetch_json(doc_url).get("service", [])
    }
    knot = services.get("#tangled_knot") or services.get("#atproto_pds")
    if not knot:
        msg = f"No tangled knot found in DID document {doc_url}"
        raise VersionError(msg)
    # self-hosted knots publish a per-repo path, but xrpc is served at the root
    endpoint = urlparse(knot)
    return f"{endpoint.scheme}://{endpoint.netloc}"


def xrpc(did: str, method: str, **params: str | int) -> dict[str, Any]:
    query = urlencode({"repo": did, **params})
    url = f"{knot_url(did)}/xrpc/org.tangled.git.{method}?{query}"
    info(f"fetch {url}")
    return fetch_json(url)


def fetch_tangled_versions(url: ParseResult) -> list[Version]:
    if not (did := tangled_did(url)):
        return []
    tags = xrpc(did, "listTags", limit=100)["tags"]
    return [Version(tag["name"]) for tag in tags]


def fetch_tangled_snapshots(url: ParseResult, branch: str) -> list[Version]:
    if not (did := tangled_did(url)):
        return []
    commits = xrpc(did, "listCommits", ref=branch, limit=1)["commits"]
    if not commits:
        msg = f"No commits found on branch {branch}"
        raise VersionError(msg)
    commit = commits[0]
    when = datetime.fromisoformat(commit["committer"]["when"])
    date = when.astimezone(UTC).date()
    bases = [version.number for version in fetch_tangled_versions(url)] + ["0"]
    return [Version(f"{base}-unstable-{date}", rev=commit["hash"]) for base in bases]
