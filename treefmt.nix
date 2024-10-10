{ inputs, ... }:
{
  imports = [ inputs.treefmt-nix.flakeModule ];

  perSystem =
    { pkgs, ... }:
    {
      treefmt = {
        # Used to find the project root
        projectRootFile = "flake.lock";

        programs.deno.enable = (builtins.tryEval pkgs.deno).success;
        programs.mypy.enable = true;

        programs.yamlfmt.enable = true;

        programs.nixfmt.enable = (builtins.tryEval pkgs.nixfmt-rfc-style).success;
        programs.deadnix.enable = true;
        programs.ruff.format = true;
        programs.ruff.check = true;

        programs.shellcheck.enable = (builtins.tryEval pkgs.shellcheck).success;
        programs.shfmt.enable = true;
        settings.formatter.shfmt.includes = [ "*.envrc" ];
      };
    };
}
