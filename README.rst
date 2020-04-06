nix-update
==========

Nix-update updates versions/source hashes of nix packages.
It is designed to work with nixpkgs but also other package sets.

Features
--------

- automatically figure out the latest version of packages from:

  - github.com
  - gitlab.com
  - pypi
- update buildRustPackage's cargoSha256
- update buildGoModule's modSha256
- build and run the resulting package (see `--build`, `--run` or `--shell` flag)
- commit updated files (see `--commit` flag)

Installation
------------

`nix-update` is included in `NUR <https://github.com/nix-community/NUR>`__.

To use it run without installing it, use:

::

   $ nix-shell -p nur.repos.mic92.nix-update

To install it:

::

   $ nix-env -f '<nixpkgs>' -iA nix-update

To run it from the git repository:

::

    $ nix-build
    $ ./result/bin/nix-update

Note that this asserts formatting with the latest version of
`black <https://github.com/psf/black>`__, so you may need to specify a more up to
date version of NixPkgs:

::

    $ nix-build -I nixpkgs=https://github.com/NixOS/nixpkgs-channels/archive/nixpkgs-unstable.tar.gz
    $ ./result/bin/nix-update

USAGE
-----

First change to your directory containing the nix expression (Could be a
nixpkgs or your own repository). Than run ``nix-update`` as follows

::

   $ nix-update attribute [version]

This example will fetch the latest github release:

::

   $ nix-update nixpkgs-review

It is also possible to specify the version manually

::

   $ nix-update --version=2.1.1 nixpkgs-review

To only update sources hashes without updating the version:

::

   $ nix-update --version=skip nixpkgs-review

With the `--shell`, `--build` and `--run` flags the update can be tested

::

   # Also runs nix-build
   $ nix-update --build nixpkgs-review
   # Also runs nix-shell
   $ nix-update --build nixpkgs-review
   # Also runs nix run
   $ nix-update --run nixpkgs-review

Nix-update also can optionally generate a commit message in the form
`attribute: old_version -> new_version` with the applied version update:

::

   $ nix-update --commit bitcoin-abc
   ...
   [master 53d68a6a5a9] bitcoin-abc: 0.21.1 -> 0.21.2
   1 file changed, 2 insertions(+), 2 deletions(-)

TODO
----

-  add tests
-  create pull requests
-  update unstable packages from git to latest master

Known Bugs
----------

nix-update might not work correctly if a file contain multiple packages as it
performs naive search and replace to update version numbers. This might be a
problem if a file contains the same version string for multiple packages.

Related projects:
-----------------

- `nixpkgs-update <https://github.com/ryantm/nixpkgs-update>`__ is optimized for
  mass-updates in nixpkgs while nix-update is better suited for interactive
  usage that might require user-intervention i.e. fixing the build and testing
  the result. nix-update is also not limited to nixpkgs.
