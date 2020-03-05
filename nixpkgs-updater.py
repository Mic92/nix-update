#!/usr/bin/env python3

import fileinput
import json
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import urlparse


def eval_attr(attr: str) -> str:
    return f"""(with import <nixpkgs> {{}};
    let
      pkg = {attr};
    in {{
      position = pkg.meta.position;
      url = pkg.src.meta.homepage;
      hash = pkg.src.outputHash;
      version = (builtins.parseDrvName pkg.name).version;
    }})"""


def fetch_latest_release(url_str: str) -> str:
    url = urlparse(url_str)
    parts = url.path.split("/")
    owner, repo = parts[1], parts[2]
    assert url.netloc == "github.com"
    resp = urllib.request.urlopen(f"https://github.com/{owner}/{repo}/releases.atom")
    tree = ET.fromstring(resp.read())
    release = tree.find(".//{http://www.w3.org/2005/Atom}entry")
    assert release is not None
    link = release.find("{http://www.w3.org/2005/Atom}link")
    assert link is not None
    href = link.attrib["href"]
    url = urlparse(href)
    return url.path.split("/")[-1]


def sed(filename: str, search: str, replace: str):
    with fileinput.FileInput(filename, inplace=True) as f:
        for line in f:
            print(line.replace(search, replace), end="")


def update(attr: str, latest_version: Optional[str]) -> None:
    res = subprocess.run(
        ["nix", "eval", "--json", eval_attr(attr)], text=True, stdout=subprocess.PIPE,
    )
    out = json.loads(res.stdout)
    current_version: str = out["version"]
    current_hash: str = out["hash"]
    filename, line = out["position"].rsplit(":", 1)

    if not latest_version:
        latest_version = fetch_latest_release(out["url"])

    if current_version != latest_version:
        sed(filename, current_version, latest_version)
    res2 = subprocess.run(
        ["nix-prefetch", "-A", attr], text=True, stdout=subprocess.PIPE
    )
    latest_hash = res2.stdout.strip()
    if current_hash != latest_hash:
        sed(filename, current_hash, latest_hash)


def main() -> None:
    if len(sys.argv) < 2:
        print(f"USAGE: {sys.argv[0]} package-name [version]")
        sys.exit(1)
    package_attr = sys.argv[1]
    package_attr = sys.argv[1]
    version = None
    if len(sys.argv) == 3:
        version = sys.argv[2]
    update(package_attr, version)


if __name__ == "__main__":
    main()
