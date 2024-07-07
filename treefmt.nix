{ inputs, ... }:
{
  imports = [ inputs.treefmt-nix.flakeModule ];

  perSystem =
    { pkgs, ... }:
    {
      treefmt = {
        # Used to find the project root
        projectRootFile = "flake.lock";

        programs.deno.enable = (pkgs.lib.meta.availableOn pkgs.stdenv.hostPlatform pkgs.deno) && !pkgs.deno.meta.broken;
        programs.mypy.enable = true;

        programs.yamlfmt.enable = true;

        programs.nixfmt.enable = pkgs.lib.meta.availableOn pkgs.stdenv.buildPlatform pkgs.nixfmt-rfc-style.compiler;
        programs.deadnix.enable = true;
        programs.ruff.format = true;
        programs.ruff.check = true;

        programs.shellcheck.enable = pkgs.lib.meta.availableOn pkgs.stdenv.buildPlatform pkgs.shellcheck.compiler;
        programs.shfmt.enable = true;
        settings.formatter.shfmt.includes = [ "*.envrc" ];
      };
    };
}
