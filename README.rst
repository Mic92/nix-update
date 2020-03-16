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
