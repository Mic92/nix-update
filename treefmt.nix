{ inputs, ... }: {
  imports = [
    inputs.treefmt-nix.flakeModule
  ];

  perSystem = { pkgs, ... }: {
    treefmt = {
      # Used to find the project root
      projectRootFile = "flake.lock";

      programs.prettier.enable = true;

      settings.formatter = {
        nix = {
          command = "sh";
          options = [
            "-eucx"
            ''
              # First deadnix
              ${pkgs.lib.getExe pkgs.deadnix} --edit "$@"
              # Then nixpkgs-fmt
              ${pkgs.lib.getExe pkgs.nixpkgs-fmt} "$@"
            ''
            "--"
          ];
          includes = [ "*.nix" ];
          excludes = [ "nix/sources.nix" ];
        };

        python = {
          command = "sh";
          options = [
            "-eucx"
            ''
              ${pkgs.lib.getExe pkgs.ruff} --fix "$@"
              ${pkgs.lib.getExe pkgs.python3.pkgs.black} "$@"
            ''
            "--" # this argument is ignored by bash
          ];
          includes = [ "*.py" ];
        };
      };
    };
  };
}
