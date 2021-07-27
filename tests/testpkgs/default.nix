{ pkgs ? import <nixpkgs> {} }:
{
  pypi = pkgs.python3.pkgs.callPackage ./pypi.nix {};
  savanna = pkgs.python3.pkgs.callPackage ./savanna.nix {};
}
