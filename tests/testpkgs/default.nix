{ pkgs ? import <nixpkgs> {} }:
{
  pypi = pkgs.python3.pkgs.callPackage ./pypi.nix {};
  sourcehut = pkgs.python3.pkgs.callPackage ./sourcehut.nix {};
  savanna = pkgs.python3.pkgs.callPackage ./savanna.nix {};
}
