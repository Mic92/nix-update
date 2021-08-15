{ pkgs ? import <nixpkgs> { } }:

with pkgs;
pkgs.mkShell {
  buildInputs = [
    (import ./. { }).passthru.env
  ];
}
