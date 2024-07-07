{
  outputs =
    { self, nixpkgs }:
    {
      packages = nixpkgs.lib.genAttrs nixpkgs.lib.systems.flakeExposed (system: {
        crate = nixpkgs.legacyPackages.${system}.callPackage (self + "/crate.nix") { };
      });
    };
}
