import fileinput
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path

from .errors import UpdateError
from .eval import CargoLockInSource, CargoLockInStore, Package, eval_attr
from .git import old_version_from_git
from .lockfile import generate_lockfile
from .options import Options
from .utils import info, run
from .version import fetch_latest_version
from .version.gitlab import GITLAB_API
from .version.version import Version, VersionPreference

# Hash length constants for SRI format conversion
MD5_HASH_LENGTH = 32
SHA1_HASH_LENGTH = 40


def replace_version(package: Package) -> bool:
    if package.new_version is None:
        msg = "Package new_version is None, cannot replace version"
        raise ValueError(msg)
    old_rev_tag = package.rev or package.tag
    old_version = package.old_version
    new_version = package.new_version.number
    new_version = new_version.removeprefix("v")

    changed = old_version != new_version or (
        package.new_version.rev is not None and package.new_version.rev != old_rev_tag
    )

    if changed:
        info(f"Update {old_version} -> {new_version} in {package.filename}")
        version_string_in_version_declaration = False
        if package.version_position is not None:
            with Path(package.filename).open() as f:
                for i, line in enumerate(f, 1):
                    if package.version_position.line == i:
                        version_string_in_version_declaration = old_version in line
                        break
        with fileinput.FileInput(package.filename, inplace=True) as f:
            for i, original_line in enumerate(f, 1):
                modified_line = original_line
                if old_rev_tag is not None and package.new_version.rev:
                    modified_line = modified_line.replace(
                        old_rev_tag,
                        package.new_version.rev,
                    )
                if not version_string_in_version_declaration or (
                    package.version_position is not None
                    and package.version_position.line == i
                ):
                    modified_line = modified_line.replace(
                        f'"{old_version}"',
                        f'"{new_version}"',
                    )
                print(modified_line, end="")
    else:
        info(f"Not updating version, already {old_version}")

    return changed


def to_sri(hashstr: str) -> str:
    if "-" in hashstr:
        return hashstr
    length = len(hashstr)
    if length == MD5_HASH_LENGTH:
        prefix = "md5:"
    elif length == SHA1_HASH_LENGTH:
        # could be also base32 == 32, but we ignore this case and hope no one is using it
        prefix = "sha1:"
    elif length in (64, 52):
        prefix = "sha256:"
    elif length in (103, 128):
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
            for original_line in f:
                modified_line = original_line.replace(current, normalized_hash)
                print(modified_line, end="")


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
                *opts.extra_flags,
            ],
            extra_env=extra_env,
            stderr=subprocess.PIPE,
            check=False,
        )
        stderr = res.stderr.strip()
        # got:    xxx
        # expected 'xxx' but got 'xxx'
        regex = re.compile(r".*got(:|\s)\s*'?([^']*)('|$)")
        got = ""
        for line in reversed(stderr.split("\n")):
            if match := regex.fullmatch(line):
                got = match[2]
                break
    finally:
        if tempdir:
            tempdir.cleanup()

    if got == "":
        print(stderr, file=sys.stderr)
        msg = f"failed to retrieve hash when trying to update {opts.attribute}.{attr}"
        raise UpdateError(msg)
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


def update_cargo_vendor_deps_hash(
    opts: Options,
    filename: str,
    current_hash: str,
) -> None:
    target_hash = nix_prefetch(opts, "cargoDeps.vendorStaging")
    replace_hash(filename, current_hash, target_hash)


def build_cargo_lock(opts: Options, tempdir: str) -> Path | None:
    res = run(
        [
            "nix",
            "build",
            "--out-link",
            f"{tempdir}/result",
            "--impure",
            "--print-out-paths",
            "--expr",
            f'\n{get_package(opts)}.overrideAttrs (old: {{\n  cargoDeps = null;\n  postUnpack = \'\'\n    cp -r "$sourceRoot/${{old.cargoRoot or "."}}/Cargo.lock" $out\n    exit\n  \'\';\n  outputs = [ "out" ];\n  separateDebugInfo = false;\n}})\n',
            *opts.extra_flags,
        ],
    )
    src = Path(res.stdout.strip())
    return src if src.is_file() else None


def process_git_dependencies(lock: dict) -> dict[str, str]:
    regex = re.compile(r"git\+([^?]+)(\?(rev|tag|branch)=.*)?#(.*)")
    git_deps = {}
    for pkg in lock["package"]:
        if (source := pkg.get("source")) and (match := regex.fullmatch(source)):
            rev = match[4]
            if rev not in git_deps:
                git_deps[rev] = f"{pkg['name']}-{pkg['version']}", match[1]

    return dict(ThreadPoolExecutor().map(git_prefetch, git_deps.items()))


def update_short_format(
    hashes: dict[str, str],
    match: re.Match[str],
    f: fileinput.FileInput[str],
) -> None:
    indent = match[1]
    path = match[2]
    print(f"{indent}cargoLock = {{")
    print(f"{indent}  lockFile = {path};")
    print_hashes(hashes, f"{indent}  ")
    print(f"{indent}}};")
    for remaining_line in f:
        print(remaining_line, end="")


def update_expanded_format(
    hashes: dict[str, str],
    match: re.Match[str],
    f: fileinput.FileInput[str],
) -> None:
    indent = match[1]
    print(match[0], end="")
    print_hashes(hashes, indent)
    brace = 0
    for next_line in f:
        for c in next_line:
            if c == "{":
                brace -= 1
            if c == "}":
                brace += 1
            if brace == 1:
                print(next_line, end="")
                for final_line in f:
                    print(final_line, end="")
                return


def update_cargo_lock(
    opts: Options,
    filename: str,
    dst: CargoLockInSource | CargoLockInStore,
) -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        src = build_cargo_lock(opts, tempdir)
        if not src:
            return

        hashes = {}
        with Path(src).open("rb") as f:
            if isinstance(dst, CargoLockInSource):
                with Path(dst.path).open("wb") as fdst:
                    shutil.copyfileobj(f, fdst)
                    f.seek(0)

            lock = tomllib.load(f)
            hashes = process_git_dependencies(lock)

    with fileinput.FileInput(filename, inplace=True) as f:
        short = re.compile(r"(\s*)cargoLock\.lockFile\s*=\s*(.+)\s*;\s*")
        expanded = re.compile(r"(\s*)lockFile\s*=\s*(.+)\s*;\s*")

        for line in f:
            if match := short.fullmatch(line):
                update_short_format(hashes, match, f)
                return
            if match := expanded.fullmatch(line):
                update_expanded_format(hashes, match, f)
                return
            print(line, end="")


def update_composer_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "composerVendor")
    replace_hash(filename, current_hash, target_hash)


def update_composer_deps_hash_old(
    opts: Options,
    filename: str,
    current_hash: str,
) -> None:
    target_hash = nix_prefetch(opts, "composerRepository")
    replace_hash(filename, current_hash, target_hash)


def print_hashes(hashes: dict[str, str], indent: str) -> None:
    if not hashes:
        return
    print(f"{indent}outputHashes = {{")
    for k, v in hashes.items():
        print(f'{indent}  "{k}" = "{v}";')
    print(f"{indent}}};")


def update_pnpm_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "pnpmDeps")
    replace_hash(filename, current_hash, target_hash)


def update_npm_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "npmDeps")
    replace_hash(filename, current_hash, target_hash)


def update_zig_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "zigDeps")
    replace_hash(filename, current_hash, target_hash)


def update_yarn_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "yarnOfflineCache")
    replace_hash(filename, current_hash, target_hash)


def update_yarn_deps_hash_old(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "offlineCache")
    replace_hash(filename, current_hash, target_hash)


def update_maven_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "fetchedMavenDeps")
    replace_hash(filename, current_hash, target_hash)


def update_mix_deps_hash(opts: Options, filename: str, current_hash: str) -> None:
    target_hash = nix_prefetch(opts, "mixFodDeps")
    replace_hash(filename, current_hash, target_hash)


def update_nuget_deps(opts: Options) -> None:
    fetch_deps_script_path = run(
        [
            "nix-build",
            opts.import_path,
            "-A",
            f"{opts.attribute}.fetch-deps",
            "--no-out-link",
        ],
    ).stdout.strip()

    run([fetch_deps_script_path])


def fetch_new_version(
    opts: Options,
    package: Package,
    version: str,
    preference: VersionPreference,
    version_regex: str,
) -> Version:
    if preference == VersionPreference.FIXED:
        return Version(version)

    if not package.parsed_url:
        msg = "Could not find a url in the derivations src attribute"
        raise UpdateError(msg)

    version_prefix = ""
    branch = None
    old_rev_tag = package.rev or package.tag

    if preference != VersionPreference.BRANCH:
        if old_rev_tag and old_rev_tag.endswith(package.old_version):
            version_prefix = old_rev_tag.removesuffix(package.old_version)
    elif version == "branch":
        branch = "HEAD"
    else:
        if not version.startswith("branch="):
            msg = f"Invalid version format: {version}, expected 'branch=' prefix"
            raise ValueError(msg)
        branch = version[7:]

    return fetch_latest_version(
        package.parsed_url,
        preference,
        version_regex,
        branch,
        old_rev_tag,
        version_prefix,
        fetcher_args={"use_github_releases": opts.use_github_releases},
    )


def create_crates_diff_url(package: Package, new_version: Version) -> str:
    if package.parsed_url is None:
        msg = "Package parsed_url is None"
        raise ValueError(msg)
    parts = package.parsed_url.path.split("/")
    return f"https://diff.rs/{parts[4]}/{package.old_version}/{new_version.number}"


def create_npm_diff_url(package: Package, new_version: Version) -> str:
    if package.parsed_url is None:
        msg = "Package parsed_url is None"
        raise ValueError(msg)
    parts = package.parsed_url.path.split("/")
    package_name = f"{parts[1]}%2F{parts[2]}" if parts[1].startswith("@") else parts[1]
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


def update_version(
    opts: Options,
    package: Package,
    version: str,
    preference: VersionPreference,
    version_regex: str,
) -> bool:
    new_version = fetch_new_version(opts, package, version, preference, version_regex)
    package.new_version = new_version

    position = package.version_position
    if new_version.number == package.old_version and position:
        recovered_version = old_version_from_git(
            position.file,
            position.line,
            new_version.number,
        )
        if recovered_version:
            package.old_version = recovered_version
            return False

    if not replace_version(package):
        return False

    generate_diff_url(opts, package, new_version)
    return True


def run_update_script(package: Package, opts: Options) -> None:
    if not opts.flake:
        run(
            [
                "nix-shell",
                *opts.extra_flags,
                str(Path(opts.import_path) / "maintainers/scripts/update.nix"),
                "--argstr",
                "package",
                opts.attribute,
                "--argstr",
                "skip-prompt",
                "true",
                *opts.update_script_args,
            ],
            stdout=None,
        )
        return

    update_script = run(
        [
            "nix",
            "build",
            *opts.extra_flags,
            "--print-out-paths",
            "--impure",
            "--expr",
            f'with import <nixpkgs> {{}}; let pkg = {get_package(opts)}; in (pkgs.writeScript "updateScript" (lib.escapeShellArgs (pkgs.lib.toList (pkg.updateScript.command or pkg.updateScript))))',
        ],
    ).stdout.strip()

    run(
        [
            "nix",
            "develop",
            *opts.extra_flags,
            "--impure",
            "--expr",
            f"with import <nixpkgs> {{}}; pkgs.mkShell {{inputsFrom = [{get_package(opts)}];}}",
            "--command",
            "bash",
            "-c",
            " ".join(
                [
                    "env",
                    f"UPDATE_NIX_NAME={package.name}",
                    f"UPDATE_NIX_PNAME={package.pname}",
                    f"UPDATE_NIX_OLD_VERSION={package.old_version}",
                    f"UPDATE_NIX_ATTR_PATH={package.attribute}",
                    update_script,
                ],
            ),
            *opts.update_script_args,
        ],
        cwd=opts.import_path,
    )


def update_dependency_hashes(  # noqa: C901, PLR0912
    opts: Options,
    package: Package,
    *,
    update_hash: bool,
) -> None:
    if not (update_hash or not package.hash) or opts.src_only:
        return

    if package.go_modules:
        update_go_modules_hash(opts, package.filename, package.go_modules)

    if package.go_modules_old:
        update_go_modules_hash_old(opts, package.filename, package.go_modules_old)

    if package.cargo_deps:
        update_cargo_deps_hash(opts, package.filename, package.cargo_deps)

    if package.cargo_vendor_deps:
        update_cargo_vendor_deps_hash(
            opts,
            package.filename,
            package.cargo_vendor_deps,
        )

    if package.composer_deps:
        update_composer_deps_hash(opts, package.filename, package.composer_deps)

    if package.composer_deps_old:
        update_composer_deps_hash_old(
            opts,
            package.filename,
            package.composer_deps_old,
        )

    if package.npm_deps:
        if opts.generate_lockfile:
            generate_lockfile(opts, package.filename, "npm", get_package(opts))
        update_npm_deps_hash(opts, package.filename, package.npm_deps)

    if package.pnpm_deps:
        update_pnpm_deps_hash(opts, package.filename, package.pnpm_deps)

    if package.yarn_deps:
        update_yarn_deps_hash(opts, package.filename, package.yarn_deps)

    if package.yarn_deps_old:
        update_yarn_deps_hash_old(opts, package.filename, package.yarn_deps_old)

    if package.maven_deps:
        update_maven_deps_hash(opts, package.filename, package.maven_deps)

    if package.mix_deps:
        update_mix_deps_hash(opts, package.filename, package.mix_deps)

    if package.has_nuget_deps:
        update_nuget_deps(opts)

    if package.zig_deps:
        update_zig_deps_hash(opts, package.filename, package.zig_deps)

    if isinstance(package.cargo_lock, CargoLockInSource | CargoLockInStore):
        if opts.generate_lockfile:
            generate_lockfile(opts, package.filename, "cargo", get_package(opts))
        else:
            update_cargo_lock(opts, package.filename, package.cargo_lock)


def update(opts: Options) -> Package:
    package = eval_attr(opts)

    if package.has_update_script and opts.use_update_script:
        run_update_script(package, opts)
        new_package = eval_attr(opts)
        package.new_version = Version(
            new_package.old_version,
            rev=new_package.rev,
            tag=new_package.tag,
        )

        return package

    update_hash = True

    if opts.version_preference != VersionPreference.SKIP:
        update_hash = update_version(
            opts,
            package,
            opts.version,
            opts.version_preference,
            opts.version_regex,
        )

    if package.hash and update_hash and opts.update_src:
        update_src_hash(opts, package.filename, package.hash)

    if opts.subpackages:
        for subpackage in opts.subpackages:
            info(f"Updating subpackage {subpackage}")
            subpackage_opts = deepcopy(opts)
            subpackage_opts.attribute += f".{subpackage}"
            # Update escaped package attribute
            subpackage_opts.__post_init__()
            subpackage_opts.subpackages = None
            # Do not update the version number since that's already been done
            subpackage_opts.version_preference = VersionPreference.SKIP
            update(subpackage_opts)

    update_dependency_hashes(opts, package, update_hash=update_hash)

    return package
