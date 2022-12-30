{pkgs ? import <nixpkgs> {}}:
with pkgs;
  mkShellNoCC {
    buildInputs = [
      (import ./. {}).passthru.env
    ];
  }
