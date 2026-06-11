{
  description = "Swiss-knife for updating nix packages.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    {
      self,
      nixpkgs,
      treefmt-nix,
    }:
    let
      inherit (nixpkgs) lib;
      systems = [
        "aarch64-linux"
        "x86_64-linux"
        "riscv64-linux"

        "x86_64-darwin"
        "aarch64-darwin"
      ];
      eachSystem = f: lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
      treefmtEval = eachSystem (pkgs: treefmt-nix.lib.evalModule pkgs ./treefmt.nix);
    in
    {
      packages = eachSystem (pkgs: rec {
        nix-update = pkgs.callPackage ./. { };
        default = nix-update;
      });

      devShells = eachSystem (pkgs: {
        default = pkgs.mkShell {
          inputsFrom = [ self.packages.${pkgs.stdenv.hostPlatform.system}.default ];
          packages = [
            (pkgs.python3.withPackages (
              ps: with ps; [
                pytest
              ]
            ))
            pkgs.mypy
            pkgs.ruff
          ];
          # Make tests use our pinned Nixpkgs
          env.NIX_PATH = "nixpkgs=${pkgs.path}";
        };
      });

      formatter = eachSystem (pkgs: treefmtEval.${pkgs.stdenv.hostPlatform.system}.config.build.wrapper);

      checks = eachSystem (
        pkgs:
        let
          system = pkgs.stdenv.hostPlatform.system;
          packages = lib.mapAttrs' (n: lib.nameValuePair "package-${n}") self.packages.${system};
          devShells = lib.mapAttrs' (n: lib.nameValuePair "devShell-${n}") self.devShells.${system};
        in
        packages
        // devShells
        // lib.optionalAttrs (system != "riscv64-linux") {
          formatting = treefmtEval.${system}.config.build.check self;
        }
        // {
          # Puts test-fixture toolchains in a runtime closure so the
          # CI binary cache (hestia) roots them.
          test-deps = pkgs.linkFarm "test-deps" {
            inherit (pkgs)
              rustc
              cargo
              cargo-auditable
              maturin
              jq
              ;
          };
        }
      );
    };
}
