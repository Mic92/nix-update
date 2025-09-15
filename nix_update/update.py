import fileinput
from copy import deepcopy
from pathlib import Path

from .dependency_hashes import update_dependency_hashes, update_src_hash
from .diff_urls import generate_diff_url
from .errors import UpdateError
from .eval import Package, eval_attr
from .git import old_version_from_git
from .options import Options
from .utils import info, run
from .version import VersionFetchConfig, fetch_latest_version
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
