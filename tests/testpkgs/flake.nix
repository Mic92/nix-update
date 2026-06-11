{
  inputs = {
    # NIXPKGS_PLACEHOLDER - This will be patched during tests to use the main flake's nixpkgs
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs =
    {
      self,
      nixpkgs,
    }:
    {
      packages = nixpkgs.lib.genAttrs nixpkgs.lib.systems.flakeExposed (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          crate = pkgs.callPackage (self + "/crate.nix") { };
          flake-use-update-script = pkgs.callPackage (self + "/flake-use-update-script.nix") { };
          nuget-deps-generate = pkgs.callPackage (self + "/nuget-deps-generate") { };
        }
      );
    };
}
