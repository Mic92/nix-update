{ inputs, ... }:
{
  imports = [ inputs.treefmt-nix.flakeModule ];

  perSystem =
    { pkgs, ... }:
    {
      treefmt = {
        # Used to find the project root
        projectRootFile = "flake.lock";

        programs.deno.enable =
          pkgs.hostPlatform.system != "x86_64-darwin" && pkgs.hostPlatform.system != "riscv64-linux";
        programs.mypy.enable = true;

        programs.yamlfmt.enable = true;

        programs.nixfmt.enable = pkgs.hostPlatform.system != "riscv64-linux";
        programs.deadnix.enable = true;
        programs.ruff.format = true;
        programs.ruff.check = true;

        programs.shellcheck.enable = pkgs.hostPlatform.system != "riscv64-linux";
        programs.shfmt.enable = true;
        settings.formatter.shfmt.includes = [ "*.envrc" ];
      };
    };
}
