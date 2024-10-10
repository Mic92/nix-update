{
  pkgs ? import <nixpkgs> { },
}:

pkgs.python3.pkgs.buildPythonApplication {
  pname = "nix-update";
  version = "1.5.2";
  src = ./.;
  format = "pyproject";
  buildInputs = [ pkgs.makeWrapper ];
  nativeBuildInputs = [ pkgs.python3.pkgs.setuptools ];
  nativeCheckInputs = [
    pkgs.python3.pkgs.pytest
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
      pkgs.nixVersions.stable
      pkgs.nixpkgs-review
      pkgs.nix-prefetch-git
    ])
  ];
}
