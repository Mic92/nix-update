{
  inputs = {
    # NIXPKGS_PLACEHOLDER - This will be patched during tests to use the main flake's nixpkgs
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    # This will be patched during tests to use the local nix-update checkout
    nix-update.url = "github:Mic92/nix-update";
    nix-update.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    {
      self,
      nixpkgs,
      nix-update,
    }:
    {
      packages = nixpkgs.lib.genAttrs nixpkgs.lib.systems.flakeExposed (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          # Run the nix-update under test instead of the one shipped in nixpkgs.
          nix-update-script = pkgs.nix-update-script.override {
            nix-update = nix-update.packages.${system}.nix-update;
          };
        in
        {
          crate = pkgs.callPackage (self + "/crate.nix") { inherit nix-update-script; };
          flake-use-update-script = pkgs.callPackage (self + "/flake-use-update-script.nix") {
            inherit nix-update-script;
          };
          nuget-deps-generate = pkgs.callPackage (self + "/nuget-deps-generate") { };
        }
      );
    };
}
