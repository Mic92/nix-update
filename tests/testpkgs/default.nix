{ pkgs ? import <nixpkgs> { } }:
{
  cargoLockExpand = pkgs.callPackage ./cargo-lock-expand { };
  cargoLockUpdate = pkgs.callPackage ./cargo-lock-update { };
  crate = pkgs.callPackage ./crate.nix { };
  gitea = pkgs.callPackage ./gitea.nix { };
  github = pkgs.callPackage ./github.nix { };
  gitlab = pkgs.callPackage ./gitlab.nix { };
  pypi = pkgs.python3.pkgs.callPackage ./pypi.nix { };
  sourcehut = pkgs.python3.pkgs.callPackage ./sourcehut.nix { };
  savanna = pkgs.python3.pkgs.callPackage ./savanna.nix { };
  npm = pkgs.callPackage ./npm.nix { };
}
