{ pkgs ? import <nixpkgs> { }
}:


pkgs.python311.pkgs.buildPythonApplication {
  name = "nix-update";
  src = ./.;
  buildInputs = [ pkgs.makeWrapper ];
  nativeCheckInputs = [
    pkgs.python311.pkgs.pytest
    # technically not test inputs, but we need it for development in PATH
    pkgs.nixVersions.stable or pkgs.nix_2_4
    pkgs.nix-prefetch-git
  ];
  checkPhase = ''
    PYTHONPATH= $out/bin/nix-update --help
  '';
  makeWrapperArgs = [
    "--prefix PATH"
    ":"
    (pkgs.lib.makeBinPath [ pkgs.nixVersions.stable or pkgs.nix_2_4 pkgs.nixpkgs-review pkgs.nix-prefetch-git ])
  ];
  shellHook = ''
    # workaround because `python setup.py develop` breaks for me
  '';
}
