import fileinput
import re
import subprocess
import sys
import tempfile
from copy import deepcopy
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from .cargo import update_cargo_lock
from .errors import UpdateError
from .eval import Package, eval_attr
from .git import old_version_from_git
from .hashes import to_sri
from .lockfile import generate_lockfile
from .options import Options
from .utils import info, run
from .version import VersionFetchConfig, fetch_latest_version
from .version.gitlab import GITLAB_API
from .version.version import Version, VersionPreference


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


def replace_hash(filename: str, current: str, target: str) -> None:
    normalized_hash = to_sri(target)
    if to_sri(current) != normalized_hash:
        with fileinput.FileInput(filename, inplace=True) as f:
            for original_line in f:
                modified_line = original_line.replace(current, normalized_hash)
                print(modified_line, end="")


def nix_prefetch(opts: Options, attr: str) -> str:
    expr = f"{opts.get_package()}.{attr}"

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


def update_hash_with_prefetch(
    attr_name: str,
    opts: Options,
    filename: str,
    current_hash: str,
) -> None:
    """Generic function to update a hash by prefetching with a specific attribute."""
    target_hash = nix_prefetch(opts, attr_name)
    replace_hash(filename, current_hash, target_hash)


# Create partial function for updating src hash (used elsewhere in the code)
update_src_hash = partial(update_hash_with_prefetch, "src")


def update_nuget_deps(opts: Options, _filename: str, _nuget_deps_path: str) -> None:
    """Update NuGet dependencies.

    The _filename and _nuget_deps_path parameters are included for API compatibility.
    _nuget_deps_path contains the path to the deps file, but we regenerate it entirely.
    """
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

    config = VersionFetchConfig(
        preference=preference,
        version_regex=version_regex,
        branch=branch,
        old_rev_tag=old_rev_tag,
        version_prefix=version_prefix,
        fetcher_args={"use_github_releases": opts.use_github_releases},
    )
    return fetch_latest_version(package.parsed_url, config)


def create_crates_diff_url(package: Package, new_version: Version) -> str:
    crates_path_min_parts = 5

    if package.parsed_url is None:
        msg = "Package parsed_url is None"
        raise UpdateError(msg)
    parts = package.parsed_url.path.split("/")
    if len(parts) < crates_path_min_parts:
        msg = f"Unexpected crates.io URL path structure: {package.parsed_url.path}"
        raise UpdateError(msg)
    return f"https://diff.rs/{parts[crates_path_min_parts - 1]}/{package.old_version}/{new_version.number}"


def create_npm_diff_url(package: Package, new_version: Version) -> str:
    npm_path_min_parts = 2
    npm_scoped_path_min_parts = 3
    npm_package_index = 1
    npm_scoped_name_index = 2

    if package.parsed_url is None:
        msg = "Package parsed_url is None"
        raise UpdateError(msg)
    parts = package.parsed_url.path.split("/")
    if len(parts) < npm_path_min_parts:
        msg = f"Unexpected npm URL path structure: {package.parsed_url.path}"
        raise UpdateError(msg)
    if parts[npm_package_index].startswith("@"):
        if len(parts) < npm_scoped_path_min_parts:
            msg = f"Unexpected scoped npm package URL structure: {package.parsed_url.path}"
            raise UpdateError(msg)
        package_name = f"{parts[npm_package_index]}%2F{parts[npm_scoped_name_index]}"
    else:
        package_name = parts[npm_package_index]
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
            f'with import <nixpkgs> {{}}; let pkg = {opts.get_package()}; in (pkgs.writeScript "updateScript" (lib.escapeShellArgs (pkgs.lib.toList (pkg.updateScript.command or pkg.updateScript))))',
        ],
    ).stdout.strip()

    run(
        [
            "nix",
            "develop",
            *opts.extra_flags,
            "--impure",
            "--expr",
            f"with import <nixpkgs> {{}}; pkgs.mkShell {{inputsFrom = [{opts.get_package()}];}}",
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


def update_dependency_hashes(
    opts: Options,
    package: Package,
    *,
    update_hash: bool,
) -> None:
    if not (update_hash or not package.hash) or opts.src_only:
        return

    hash_updaters: dict[str, Callable[[Options, str, Any], None]] = {
        "go_modules": partial(update_hash_with_prefetch, "goModules"),
        "go_modules_old": partial(update_hash_with_prefetch, "go-modules"),
        "cargo_deps": partial(update_hash_with_prefetch, "cargoDeps"),
        "cargo_vendor_deps": partial(
            update_hash_with_prefetch,
            "cargoDeps.vendorStaging",
        ),
        "composer_deps": partial(update_hash_with_prefetch, "composerVendor"),
        "composer_deps_old": partial(update_hash_with_prefetch, "composerRepository"),
        "npm_deps": (lambda o, f, _d: generate_lockfile(o, f, "npm", o.get_package()))
        if opts.generate_lockfile
        else partial(update_hash_with_prefetch, "npmDeps"),
        "pnpm_deps": partial(update_hash_with_prefetch, "pnpmDeps"),
        "yarn_deps": partial(update_hash_with_prefetch, "yarnOfflineCache"),
        "yarn_deps_old": partial(update_hash_with_prefetch, "offlineCache"),
        "maven_deps": partial(update_hash_with_prefetch, "fetchedMavenDeps"),
        "mix_deps": partial(update_hash_with_prefetch, "mixFodDeps"),
        "zig_deps": partial(update_hash_with_prefetch, "zigDeps"),
        "nuget_deps": update_nuget_deps,
        "cargo_lock": update_cargo_lock,
    }

    # Update all dependency hashes using registry
    for attr_name, updater in hash_updaters.items():
        dep_value = getattr(package, attr_name, None)
        if dep_value:
            updater(opts, package.filename, dep_value)


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
