{
  pkgs ? import <nixpkgs> { },
}:

pkgs.python311.pkgs.buildPythonApplication {
  pname = "nix-update";
  version = "1.0.0";
  src = ./.;
  format = "pyproject";
  buildInputs = [ pkgs.makeWrapper ];
  nativeBuildInputs = [ pkgs.python311.pkgs.setuptools ];
  nativeCheckInputs = [
    pkgs.python311.pkgs.pytest
    # technically not test inputs, but we need it for development in PATH
    pkgs.nixVersions.stable
    pkgs.nix-prefetch-git
  ];
  checkPhase = ''
    PYTHONPATH= $out/bin/nix-update --help
  '';
  makeWrapperArgs = [
    "--prefix PATH"
    ":"
    (pkgs.lib.makeBinPath [
      pkgs.nixVersions.stable or pkgs.nix_2_4
      pkgs.nixpkgs-review
      pkgs.nix-prefetch-git
    ])
  ];
  shellHook = ''
    # workaround because `python setup.py develop` breaks for me
  '';
}
