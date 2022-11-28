# nix-update

Nix-update updates versions/source hashes of nix packages. It is
designed to work with nixpkgs but also other package sets.

## Features

-   automatically figure out the latest version of packages from:
    -   crates.io
    -   github.com
    -   gitlab.com or other instances that uses fetchFromGitLab
    -   pypi
    -   rubygems.org
-   update buildRustPackage's cargoHash/cargoSha256 and cargoSetupHook's cargoDeps
-   update buildGoModule's vendorHash/vendorSha256
-   update buildNpmPackage's npmDepsHash and npmConfigHook's npmDeps
-   build and run the resulting package (see `--build`,
    `--run` or `--shell`
-   commit updated files (see `--commit` flag)
-   run update scripts (`passthru.updateScript`, see `--use-update-script` flag)
-   run package tests (see `--test` flag)

## Installation

`nix-update` is included in nixpkgs (unstable channel, right
now) or [NUR](https://github.com/nix-community/NUR)
(nur.repos.mic92.nix-update).

To use it run without installing it, use:

```console
$ nix-shell -p nix-update
```

To install it:

```console
$ nix-env -f '<nixpkgs>' -iA nix-update
```

To run it from the git repository:

```console
$ nix-build
$ ./result/bin/nix-update
```

If you have nix flakes enabled you can also do:

```console
$ nix run github:Mic92/nix-update
```

Note that this asserts formatting with the latest version of
[black](https://github.com/psf/black), so you may need to specify a more
up to date version of NixPkgs:

```console
$ nix-build -I nixpkgs=https://github.com/NixOS/nixpkgs-channels/archive/nixpkgs-unstable.tar.gz
$ ./result/bin/nix-update
```

## USAGE

First change to your directory containing the nix expression (Could be a
nixpkgs or your own repository). Than run `nix-update` as follows

```console
$ nix-update attribute [--version version]
```

This example will fetch the latest github release:

```console
$ nix-update nixpkgs-review
```

It is also possible to specify the version manually

```console
$ nix-update --version=2.1.1 nixpkgs-review
```

To only update sources hashes without updating the version:

```console
$ nix-update --version=skip nixpkgs-review
```

To extract version information from versions with prefixes or suffixes,
a regex can be used

```console
$ nix-update jq --version-regex 'jq-(.*)'
```

By default `nix-update` will locate the file that needs to be patched using the `src` attribute of a derivation.
In some cases this heurestic is wrong. One can override the behavior like that:

``` console
$ nix-update hello --override-filename pkgs/applications/misc/hello/default.nix
```

With the `--shell`, `--build`, `--test` and `--run` flags the update can be
tested. Additionally, the `--review` flag can be used to
initiate a run of [nixpkgs-review](https://github.com/Mic92/nixpkgs-review), which will ensure all
dependent packages can be built. In order to ensure consistent
formatting, the `--format` flag will invoke
[nixpkgs-fmt](<https://github.com/nix-community/nixpkgs-fmt>).

```console
# Also runs nix-build
$ nix-update --build nixpkgs-review
# Also runs nix-build nixpkgs-review.tests
$ nix-update --test nixpkgs-review
# Also runs nix-shell
$ nix-update --shell nixpkgs-review
# Also runs nix run
$ nix-update --run nixpkgs-review
# Run `nixpkgs-review wip` to validate dependent packages
$ nix-update --review nixpkgs-review
# Format file
$ nix-update --format nixpkgs-review
```

Nix-update also can optionally generate a commit message in the form
`attribute: old_version -> new_version` with the applied
version update:

```console
$ nix-update --commit bitcoin-abc
...
[master 53d68a6a5a9] bitcoin-abc: 0.21.1 -> 0.21.2
1 file changed, 2 insertions(+), 2 deletions(-)
```

By default, nix-update will attempt to update to the next stable version
of a package. Alphas, betas, release candidates and similar unstable
releases will be ignored. This can be affected by changing the parameter
`version` from its default value `stable` to `unstable`.

```console
$ nix-update sbt
Not updating version, already 1.4.6

$ nix-update sbt --version=unstable
Update 1.4.6 -> 1.5.0-M1 in sbt
```

## TODO

-   create pull requests
-   update unstable packages from git to latest master

## Known Bugs

nix-update might not work correctly if a file contain multiple packages
as it performs naive search and replace to update version numbers. This
might be a problem if:

-   A file contains the same version string for multiple packages.
-   `name` is used instead of `pname` and/or `${version}` is injected into `name`.

Related discussions:

-   <https://github.com/repology/repology-updater/issues/854>
-   <https://github.com/NixOS/nixpkgs/issues/68531#issuecomment-533760929>

## Related projects:

-   [nixpkgs-update](https://github.com/ryantm/nixpkgs-update) is
    optimized for mass-updates in nixpkgs while nix-update is better
    suited for interactive usage that might require user-intervention
    i.e. fixing the build and testing the result. nix-update is also not
    limited to nixpkgs.
