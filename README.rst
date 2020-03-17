nix-update
==========

Update nix packages likes it is 2020. This tool is still in early
development.

Dependencies
------------

-  python 3
-  `nix-prefetch <https://github.com/msteen/nix-prefetch/>`__

Features
--------

- automatically figure out the latest version of packages from:

  - github.com
  - gitlab.com
  - pypi
- update buildRustPackage's cargoSha256
- update buildGoModule's modSha256
- build and run the resulting package (see `--build`, `--run` or `--shell` flag)

Installation
------------

`nix-update` is included in [NUR](https://github.com/nix-community/NUR).

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
[black](https://github.com/psf/black), so you may need to specify a more up to
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

   $ nix-update nixpkgs-review 2.1.1

TODO
----

-  ☐ optionally commit update
-  ☐ update unstable packages from git to latest master
