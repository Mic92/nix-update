{ inputs, ... }:
{
  imports = [ inputs.treefmt-nix.flakeModule ];

  perSystem =
    { pkgs, ... }:
    {
      treefmt = {
        flakeCheck = pkgs.stdenv.hostPlatform.system != "riscv64-linux";

        # Used to find the project root
        projectRootFile = "flake.lock";

        programs.deno.enable = pkgs.stdenv.hostPlatform.system != "x86_64-darwin";
        programs.mypy.enable = true;

        programs.yamlfmt.enable = true;

        programs.nixfmt.enable = true;
        programs.deadnix.enable = true;
        programs.ruff.format = true;
        programs.ruff.check = true;

        programs.shellcheck.enable = true;
        programs.shfmt.enable = true;
        settings.formatter.shfmt.includes = [ "*.envrc" ];
      };
    };
}
