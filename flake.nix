{
  description = "Swiss-knife for updating nix packages.";

  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachSystem flake-utils.lib.allSystems (system: {
      packages.nix-update = nixpkgs.legacyPackages.${system}.callPackage ./. {};
      defaultPackage = self.packages.${system}.nix-update;
    });
}
