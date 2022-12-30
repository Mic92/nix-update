{
  description = "Swiss-knife for updating nix packages.";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: {
      formatter = nixpkgs.legacyPackages.${system}.alejandra;

      packages = {
        default = self.packages.${system}.nix-update;

        nix-update = nixpkgs.legacyPackages.${system}.callPackage self {
          src = self;
        };
      };
    });
}
