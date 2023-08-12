{
  description = "Swiss-knife for updating nix packages.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-parts.inputs.nixpkgs-lib.follows = "nixpkgs";

    treefmt-nix.url = "github:numtide/treefmt-nix/mypy";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs @ { flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } ({ lib, ... }: {
      imports = [ ./treefmt.nix ];
      systems = lib.systems.flakeExposed;
      perSystem = { config, pkgs, ... }: {
        packages.nix-update = pkgs.callPackage ./. { };
        packages.default = config.packages.nix-update;
      };
    });
}
