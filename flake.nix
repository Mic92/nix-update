{
  description = "Swiss-knife for updating nix packages.";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system: {
      packages.nix-update = nixpkgs.legacyPackages.${system}.callPackage self {
        src = self;
      };
      defaultPackage = self.packages.${system}.nix-update;
    });
}
