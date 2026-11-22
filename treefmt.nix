{ pkgs }:
let
  inherit (pkgs) lib;
  mypy = pkgs.python3.withPackages (ps: [
    ps.mypy
    ps.pytest
  ]);
  shell = [
    "*.sh"
    "*.envrc"
  ];
  python = [
    "*.py"
    "*.pyi"
  ];
in
pkgs.treefmt.withConfig {
  settings = {
    tree-root-file = "flake.lock";
    excludes = [
      "*.lock"
      "*.patch"
      "go.mod"
      "go.sum"
      "package-lock.json"
      "tests/testpkgs/custom-deps/pnpm/pnpm-lock.yaml"
    ];
    formatter = {
      deadnix = {
        command = lib.getExe pkgs.deadnix;
        options = [ "--edit" ];
        includes = [ "*.nix" ];
      };
      deno = {
        command = lib.getExe pkgs.deno;
        options = [ "fmt" ];
        includes = [
          "*.json"
          "*.md"
          "*.yaml"
          "*.yml"
        ];
      };
      mypy = {
        # mypy takes its targets from pyproject.toml, not from treefmt
        command = pkgs.writeShellScript "mypy" "exec ${mypy}/bin/mypy";
        includes = [ "*.py" ];
      };
      nixfmt = {
        command = lib.getExe pkgs.nixfmt;
        includes = [ "*.nix" ];
      };
      ruff-check = {
        command = lib.getExe pkgs.ruff;
        options = [
          "check"
          "--fix"
        ];
        includes = python;
      };
      ruff-format = {
        command = lib.getExe pkgs.ruff;
        options = [ "format" ];
        includes = python;
      };
      shellcheck = {
        command = lib.getExe pkgs.shellcheck;
        includes = shell;
      };
      shfmt = {
        command = lib.getExe pkgs.shfmt;
        options = [
          "-w"
          "-i"
          "2"
          "-s"
        ];
        includes = shell;
      };
      yamlfmt = {
        command = lib.getExe pkgs.yamlfmt;
        includes = [
          "*.yaml"
          "*.yml"
        ];
      };
    };
  };
}
