#!/usr/bin/env python3

import argparse
import fileinput
import json
import re
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
import tempfile
import sys
from typing import Optional, List, NoReturn
from urllib.parse import urlparse, ParseResult


def die(msg: str) -> NoReturn:
    print(msg, file=sys.stderr)
    sys.exit(1)


def fetch_latest_github_release(url: ParseResult) -> Optional[str]:
    parts = url.path.split("/")
    owner, repo = parts[1], parts[2]
    # TODO fallback to tags?
    resp = urllib.request.urlopen(f"https://github.com/{owner}/{repo}/releases.atom")
    tree = ET.fromstring(resp.read())
    release = tree.find(".//{http://www.w3.org/2005/Atom}entry")
    if release is None:
        return None
    link = release.find("{http://www.w3.org/2005/Atom}link")
    assert link is not None
    href = link.attrib["href"]
    url = urlparse(href)
    return url.path.split("/")[-1]


def fetch_latest_pypi_release(url: ParseResult) -> str:
    parts = url.path.split("/")
    package = parts[2]
    resp = urllib.request.urlopen(f"https://pypi.org/pypi/{package}/json")
    data = json.loads(resp.read())
    return data["info"]["version"]


def fetch_latest_gitlab_release(url: ParseResult) -> Optional[str]:
    parts = url.path.split("/")
    project_id = parts[4]
    resp = urllib.request.urlopen(f"https://gitlab.com/api/v4/projects/{project_id}/repository/tags")
    data = json.loads(resp.read())
    if len(data) == 0:
        return None
    return data[0]["name"]


def fetch_latest_release(url_str: str) -> Optional[str]:
    url = urlparse(url_str)

    if url.netloc == "pypi":
        return fetch_latest_pypi_release(url)
    elif url.netloc == "github.com":
        return fetch_latest_github_release(url)
    elif url.netloc == "gitlab.com":
        return fetch_latest_gitlab_release(url)
    else:
        die(
            "Please specify the version. We can only get the latest version from github/pypi projects right now"
        )


# def find_repology_release(attr) -> str:
#    resp = urllib.request.urlopen(f"https://repology.org/api/v1/projects/{attr}/")
#    data = json.loads(resp.read())
#    for name, pkg in data.items():
#        for repo in pkg:
#            if repo["status"] == "newest":
#                return repo["version"]
#    return None


def eval_attr(import_path: str, attr: str) -> str:
    return f"""(with import {import_path} {{}};
    let
      pkg = {attr};
    in {{
      name = pkg.name;
      version = (builtins.parseDrvName pkg.name).version;
      position = pkg.meta.position;
      urls = pkg.src.urls;
      hash = pkg.src.outputHash;
      modSha256 = pkg.modSha256 or null;
      cargoSha256 = pkg.cargoSha256 or null;
    }})"""


def update_version(filename: str, current: str, target: str):
    if target.startswith("v"):
        target = target[1:]

    if current != target:
        with fileinput.FileInput(filename, inplace=True) as f:
            for line in f:
                print(line.replace(current, target), end="")


def replace_hash(filename: str, current: str, target: str):
    if current != target:
        with fileinput.FileInput(filename, inplace=True) as f:
            for line in f:
                line = re.sub(current, target, line)
                print(line, end="")


def nix_prefetch(cmd: List[str]) -> str:
    res = subprocess.run(
        ["nix-prefetch"] + cmd, text=True, stdout=subprocess.PIPE, check=True,
    )
    return res.stdout.strip()


def update_src_hash(import_path: str, attr: str, filename: str, current_hash: str):
    target_hash = nix_prefetch([f"(import {import_path} {{}}).{attr}"])
    replace_hash(filename, current_hash, target_hash)


def update_mod256_hash(import_path: str, attr: str, filename: str, current_hash: str):
    expr = f"{{ sha256 }}: (import {import_path} {{}}).{attr}.go-modules.overrideAttrs (_: {{ modSha256 = sha256; }})"
    target_hash = nix_prefetch([expr])
    replace_hash(filename, current_hash, target_hash)


def update_cargoSha256_hash(import_path: str, attr: str, filename: str, current_hash: str):
    target_hash = nix_prefetch([f"{{ sha256 }}: (import {import_path} {{}}).{attr}.cargoDeps.overrideAttrs (_: {{ inherit sha256; }})"])
    replace_hash(filename, current_hash, target_hash)


def update(import_path: str, attr: str, target_version: Optional[str]) -> None:
    res = subprocess.run(
        ["nix", "eval", "--json", eval_attr(import_path, attr)],
        text=True,
        stdout=subprocess.PIPE,
    )
    out = json.loads(res.stdout)
    current_version: str = out["version"]
    if current_version == "":
        name = out["name"]
        die(f"Nix's builtins.parseDrvName could not parse the version from {name}")
    filename, line = out["position"].rsplit(":", 1)

    if not target_version:
        # latest_version = find_repology_release(attr)
        # if latest_version is None:
        url = out["urls"][0]
        target_version = fetch_latest_release(url)
        if target_version is None:
            die("No releases found")
    update_version(filename, current_version, target_version)

    update_src_hash(import_path, attr, filename, out["hash"])

    if out["modSha256"]:
        update_mod256_hash(import_path, attr, filename, out["modSha256"])

    if out["cargoSha256"]:
        update_cargoSha256_hash(import_path, attr, filename, out["cargoSha256"])


def parse_args():
    parser = argparse.ArgumentParser()
    help = "File to import rather than default.nix. Examples, ./release.nix"
    parser.add_argument("-f", "--file", default="./.", help=help)
    parser.add_argument("--build", action="store_true", help="build the package")
    parser.add_argument(
        "--run",
        action="store_true",
        help="provide a shell based on `nix run` with the package in $PATH",
    )
    parser.add_argument(
        "--shell", action="store_true", help="provide a shell with the package"
    )
    parser.add_argument("attribute", help="Attribute name within the file evaluated")
    parser.add_argument("version", nargs="?", help="Version to update to")
    return parser.parse_args()


def nix_shell(filename: str, attribute: str) -> None:
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write(
            f"""
        with import {filename}; mkShell {{ buildInputs = [ {attribute} ]; }}
        """
        )
        f.flush()
        subprocess.run(["nix-shell", f.name])


def main() -> None:
    args = parse_args()
    update(args.file, args.attribute, args.version)
    if args.build:
        subprocess.run(["nix", "build", "-f", args.file, args.attribute])
    if args.run:
        subprocess.run(["nix", "run", "-f", args.file, args.attribute])

    if args.shell:
        nix_shell(args.file, args.attribute)


if __name__ == "__main__":
    main()
