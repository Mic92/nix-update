import fileinput
import subprocess
import tempfile
from os import path
from typing import Dict, Optional

from .errors import UpdateError
from .eval import Package, eval_attr
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

    if old_version != new_version:
        info(f"Update {old_version} -> {new_version} in {package.filename}")
        with fileinput.FileInput(package.filename, inplace=True) as f:
            for line in f:
                if package.new_version.rev:
                    line = line.replace(package.rev, package.new_version.rev)
                print(line.replace(old_version, new_version), end="")
    else:
        info(f"Not updating version, already {old_version}")

    return old_version != new_version


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


def nix_prefetch(expr: str) -> str:
    extra_env: Dict[str, str] = {}
    tempdir: Optional[tempfile.TemporaryDirectory[str]] = None
    if extra_env.get("XDG_RUNTIME_DIR") is None:
        tempdir = tempfile.TemporaryDirectory()
        extra_env["XDG_RUNTIME_DIR"] = tempdir.name
    try:
        res = run(
            [
                "nix-build",
                "--expr",
                f'let src = {expr}; in (src.overrideAttrs or (f: src // f src)) (_: {{ outputHash = ""; outputHashAlgo = "sha256"; }})',
            ],
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
    return got


def disable_check_meta(opts: Options) -> str:
    return f'(if (builtins.hasAttr "config" (builtins.functionArgs (import {opts.import_path}))) then {{ config.checkMeta = false; overlays = []; }} else {{ }})'


def get_attr(opts: Options, attr: str) -> str:
    return (
        f'let flake = builtins.getFlake "{opts.import_path}"; in (flake.packages.${{builtins.currentSystem}}.{opts.attribute} or flake.{opts.attribute}).{attr}'
        if opts.flake
        else f"(import {opts.import_path} {disable_check_meta(opts)}).{opts.attribute}.{attr}"
    )


def update_src_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(get_attr(opts, "src"))
    replace_hash(filename, current_hash, target_hash)


def update_go_modules_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(get_attr(opts, "go-modules"))
    replace_hash(filename, current_hash, target_hash)


def update_cargo_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(get_attr(opts, "cargoDeps"))
    replace_hash(filename, current_hash, target_hash)


def update_npm_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(get_attr(opts, "npmDeps"))
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
        if package.parsed_url.netloc == "github.com":
            _, owner, repo, *_ = package.parsed_url.path.split("/")
            package.diff_url = f"https://github.com/{owner}/{repo}/compare/{package.rev}...{new_version.rev or new_version.number}"
        elif GITLAB_API.match(package.parsed_url.geturl()) and package.src_homepage:
            package.diff_url = f"{package.src_homepage}-/compare/{package.rev}...{new_version.rev or new_version.number}"

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
        if package.vendor_hash and package.vendor_sha256 == "_unset":
            update_go_modules_hash(opts, package.filename, package.vendor_hash)

        if package.vendor_sha256 and package.vendor_hash == "_unset":
            update_go_modules_hash(opts, package.filename, package.vendor_sha256)

        if package.cargo_deps:
            update_cargo_deps_hash(opts, package.filename, package.cargo_deps)

        if package.npm_deps:
            update_npm_deps_hash(opts, package.filename, package.npm_deps)

    return package
