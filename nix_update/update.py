import fileinput
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from concurrent.futures import ThreadPoolExecutor
from os import path
from pathlib import Path

from .errors import UpdateError
from .eval import CargoLockInSource, CargoLockInStore, Package, eval_attr
from .git import old_version_from_git
from .options import Options
from .utils import info, run
from .version import fetch_latest_version
from .version.gitlab import GITLAB_API
from .version.version import Version, VersionPreference


def replace_version(package: Package) -> bool:
    assert package.new_version is not None
    old_version = package.old_version
    new_version = package.new_version.number
    if new_version.startswith("v"):
        new_version = new_version[1:]

    changed = old_version != new_version or (
        package.new_version.rev is not None and package.new_version.rev != package.rev
    )

    if changed:
        info(f"Update {old_version} -> {new_version} in {package.filename}")
        with fileinput.FileInput(package.filename, inplace=True) as f:
            for line in f:
                if package.new_version.rev:
                    line = line.replace(package.rev, package.new_version.rev)
                print(line.replace(f'"{old_version}"', f'"{new_version}"'), end="")
    else:
        info(f"Not updating version, already {old_version}")

    return changed


def to_sri(hashstr: str) -> str:
    if "-" in hashstr:
        return hashstr
    length = len(hashstr)
    if length == 32:
        prefix = "md5:"
    elif length == 40:
        # could be also base32 == 32, but we ignore this case and hope no one is using it
        prefix = "sha1:"
    elif length == 64 or length == 52:
        prefix = "sha256:"
    elif length == 103 or length == 128:
        prefix = "sha512:"
    else:
        return hashstr

    cmd = [
        "nix",
        "--extra-experimental-features",
        "nix-command",
        "hash",
        "to-sri",
        f"{prefix}{hashstr}",
    ]
    proc = run(cmd)
    return proc.stdout.rstrip("\n")


def replace_hash(filename: str, current: str, target: str) -> None:
    normalized_hash = to_sri(target)
    if to_sri(current) != normalized_hash:
        with fileinput.FileInput(filename, inplace=True) as f:
            for line in f:
                line = line.replace(current, normalized_hash)
                print(line, end="")


def get_package(opts: Options) -> str:
    return (
        f"(let flake = builtins.getFlake {opts.escaped_import_path}; in flake.packages.${{builtins.currentSystem}}.{opts.escaped_attribute} or flake.{opts.escaped_attribute})"
        if opts.flake
        else f"(import {opts.escaped_import_path} {disable_check_meta(opts)}).{opts.escaped_attribute}"
    )


def nix_prefetch(opts: Options, attr: str) -> str:
    expr = f"{get_package(opts)}.{attr}"

    extra_env: dict[str, str] = {}
    tempdir: tempfile.TemporaryDirectory[str] | None = None
    stderr = ""
    if extra_env.get("XDG_RUNTIME_DIR") is None:
        tempdir = tempfile.TemporaryDirectory()
        extra_env["XDG_RUNTIME_DIR"] = tempdir.name
    try:
        res = run(
            [
                "nix-build",
                "--expr",
                f'let src = {expr}; in (src.overrideAttrs or (f: src // f src)) (_: {{ outputHash = ""; outputHashAlgo = "sha256"; }})',
            ]
            + opts.extra_flags,
            extra_env=extra_env,
            stderr=subprocess.PIPE,
            check=False,
        )
        stderr = res.stderr.strip()
        got = ""
        for line in stderr.split("\n"):
            line = line.strip()
            if line.startswith("got:"):
                got = line.split("got:")[1].strip()
                break
    finally:
        if tempdir:
            tempdir.cleanup()

    if got == "":
        print(stderr, file=sys.stderr)
        raise UpdateError(
            f"failed to retrieve hash when trying to update {opts.attribute}.{attr}"
        )
    else:
        return got


def disable_check_meta(opts: Options) -> str:
    return f'(if (builtins.hasAttr "config" (builtins.functionArgs (import {opts.escaped_import_path}))) then {{ config.checkMeta = false; overlays = []; }} else {{ }})'


def git_prefetch(x: tuple[str, tuple[str, str]]) -> tuple[str, str]:
    rev, (key, url) = x
    res = run(["nix-prefetch-git", url, rev, "--fetch-submodules"])
    return key, to_sri(json.loads(res.stdout)["sha256"])


def update_src_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "src")
    replace_hash(filename, current_hash, target_hash)


def update_go_modules_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "goModules")
    replace_hash(filename, current_hash, target_hash)


def update_go_modules_hash_old(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "go-modules")
    replace_hash(filename, current_hash, target_hash)


def update_cargo_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "cargoDeps")
    replace_hash(filename, current_hash, target_hash)


def update_cargo_lock(
    opts: Options, filename: str, dst: CargoLockInSource | CargoLockInStore
) -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        res = run(
            [
                "nix",
                "build",
                "--out-link",
                f"{tempdir}/result",
                "--impure",
                "--print-out-paths",
                "--expr",
                f"""
{get_package(opts)}.overrideAttrs (old: {{
  cargoDeps = null;
  postUnpack = ''
    cp -r "$sourceRoot/${{old.cargoRoot or "."}}/Cargo.lock" $out
    exit
  '';
  outputs = [ "out" ];
}})
""",
            ]
            + opts.extra_flags,
        )
        src = Path(res.stdout.strip())
        if not src.is_file():
            return

        with open(src, "rb") as f:
            if isinstance(dst, CargoLockInSource):
                with open(dst.path, "wb") as fdst:
                    shutil.copyfileobj(f, fdst)
                    f.seek(0)

            hashes = {}
            lock = tomllib.load(f)
            regex = re.compile(r"git\+([^?]+)(\?(rev|tag|branch)=.*)?#(.*)")
            git_deps = {}
            for pkg in lock["package"]:
                if source := pkg.get("source"):
                    if match := regex.fullmatch(source):
                        rev = match[4]
                        if rev not in git_deps:
                            git_deps[rev] = f"{pkg['name']}-{pkg['version']}", match[1]

            for k, v in ThreadPoolExecutor().map(git_prefetch, git_deps.items()):
                hashes[k] = v

    with fileinput.FileInput(filename, inplace=True) as f:
        short = re.compile(r"(\s*)cargoLock\.lockFile\s*=\s*(.+)\s*;\s*")
        expanded = re.compile(r"(\s*)lockFile\s*=\s*(.+)\s*;\s*")

        for line in f:
            if match := short.fullmatch(line):
                indent = match[1]
                path = match[2]
                print(f"{indent}cargoLock = {{")
                print(f"{indent}  lockFile = {path};")
                print_hashes(hashes, f"{indent}  ")
                print(f"{indent}}};")
                for line in f:
                    print(line, end="")
                return
            elif match := expanded.fullmatch(line):
                indent = match[1]
                path = match[2]
                print(line, end="")
                print_hashes(hashes, indent)
                brace = 0
                for line in f:
                    for c in line:
                        if c == "{":
                            brace -= 1
                        if c == "}":
                            brace += 1
                        if brace == 1:
                            print(line, end="")
                            for line in f:
                                print(line, end="")
                            return
            else:
                print(line, end="")


def update_composer_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "composerRepository")
    replace_hash(filename, current_hash, target_hash)


def print_hashes(hashes: dict[str, str], indent: str) -> None:
    if not hashes:
        return
    print(f"{indent}outputHashes = {{")
    for k, v in hashes.items():
        print(f'{indent}  "{k}" = "{v}";')
    print(f"{indent}}};")


def update_npm_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "npmDeps")
    replace_hash(filename, current_hash, target_hash)


def update_yarn_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "offlineCache")
    replace_hash(filename, current_hash, target_hash)


def update_version(
    package: Package, version: str, preference: VersionPreference, version_regex: str
) -> bool:
    if preference == VersionPreference.FIXED:
        new_version = Version(version)
    else:
        if not package.parsed_url:
            raise UpdateError("Could not find a url in the derivations src attribute")

        version_prefix = ""
        if preference != VersionPreference.BRANCH:
            branch = None
            if package.rev and package.rev.endswith(package.old_version):
                version_prefix = package.rev.removesuffix(package.old_version)
        elif version == "branch":
            # fallback
            branch = "HEAD"
        else:
            assert version.startswith("branch=")
            branch = version[7:]
        new_version = fetch_latest_version(
            package.parsed_url,
            preference,
            version_regex,
            branch,
            package.rev,
            version_prefix,
        )
    package.new_version = new_version
    position = package.version_position
    if new_version.number == package.old_version and position:
        recovered_version = old_version_from_git(
            position.file, position.line, new_version.number
        )
        if recovered_version:
            package.old_version = recovered_version
            return False

    if package.parsed_url:
        if package.parsed_url.netloc == "crates.io":
            parts = package.parsed_url.path.split("/")
            package.diff_url = (
                f"https://diff.rs/{parts[4]}/{package.old_version}/{new_version.number}"
            )
        elif package.parsed_url.netloc == "github.com":
            _, owner, repo, *_ = package.parsed_url.path.split("/")
            package.diff_url = f"https://github.com/{owner}/{repo.removesuffix('.git')}/compare/{package.rev}...{new_version.rev or new_version.number}"
        elif package.parsed_url.netloc in ["codeberg.org", "gitea.com", "notabug.org"]:
            _, owner, repo, *_ = package.parsed_url.path.split("/")
            package.diff_url = f"https://{package.parsed_url.netloc}/{owner}/{repo}/compare/{package.rev}...{new_version.rev or new_version.number}"
        elif GITLAB_API.match(package.parsed_url.geturl()) and package.src_homepage:
            package.diff_url = f"{package.src_homepage}-/compare/{package.rev}...{new_version.rev or new_version.number}"
        elif package.parsed_url.netloc in ["bitbucket.org", "bitbucket.io"]:
            _, owner, repo, *_ = package.parsed_url.path.split("/")
            package.diff_url = f"https://{package.parsed_url.netloc}/{owner}/{repo}/branches/compare/{new_version.rev or new_version.number}%0D{package.rev}"

    return replace_version(package)


def update(opts: Options) -> Package:
    package = eval_attr(opts)

    if package.has_update_script and opts.use_update_script:
        run(
            [
                "nix-shell",
                path.join(opts.import_path, "maintainers/scripts/update.nix"),
                "--argstr",
                "package",
                opts.attribute,
            ],
            stdout=None,
        )

        new_package = eval_attr(opts)
        package.new_version = Version(new_package.old_version, rev=new_package.rev)

        return package

    update_hash = True

    if opts.version_preference != VersionPreference.SKIP:
        update_hash = update_version(
            package, opts.version, opts.version_preference, opts.version_regex
        )

    if package.hash and update_hash:
        update_src_hash(opts, package.filename, package.hash)

    # if no package.hash was provided we just update the other hashes unconditionally
    if update_hash or not package.hash:
        if package.go_modules:
            update_go_modules_hash(opts, package.filename, package.go_modules)

        if package.go_modules_old:
            update_go_modules_hash_old(opts, package.filename, package.go_modules_old)

        if package.cargo_deps:
            update_cargo_deps_hash(opts, package.filename, package.cargo_deps)

        if isinstance(package.cargo_lock, CargoLockInSource) or isinstance(
            package.cargo_lock, CargoLockInStore
        ):
            update_cargo_lock(opts, package.filename, package.cargo_lock)

        if package.composer_deps:
            update_composer_deps_hash(opts, package.filename, package.composer_deps)

        if package.npm_deps:
            update_npm_deps_hash(opts, package.filename, package.npm_deps)

        if package.yarn_deps:
            update_yarn_deps_hash(opts, package.filename, package.yarn_deps)

    return package
