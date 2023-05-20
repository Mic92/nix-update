{ pkgs ? import <nixpkgs> { }
}:


pkgs.python311.pkgs.buildPythonApplication {
  name = "nix-update";
  src = ./.;
  buildInputs = [ pkgs.makeWrapper ];
  nativeCheckInputs = [
    pkgs.python311.pkgs.pytest
    pkgs.python311.pkgs.black
    pkgs.ruff
    pkgs.glibcLocales
    pkgs.mypy
    # technically not test inputs, but we need it for development in PATH
    pkgs.nixVersions.stable or pkgs.nix_2_4
    pkgs.nix-prefetch-git
  ];
  checkPhase = ''
    echo -e "\x1b[32m## run black\x1b[0m"
    LC_ALL=en_US.utf-8 black --check . bin/nix-update
    echo -e "\x1b[32m## run ruff\x1b[0m"
    ruff . bin/nix-update
    echo -e "\x1b[32m## run mypy\x1b[0m"
    mypy --no-warn-unused-ignores --strict nix_update tests
  '';
  makeWrapperArgs = [
    "--prefix PATH"
    ":"
    (pkgs.lib.makeBinPath [ pkgs.nixVersions.stable or pkgs.nix_2_4 pkgs.nixpkgs-fmt pkgs.nixpkgs-review pkgs.nix-prefetch-git ])
  ];
  shellHook = ''
    # workaround because `python setup.py develop` breaks for me
  '';
}
