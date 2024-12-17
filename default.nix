{
  pkgs ? import <nixpkgs> { },
}:
pkgs.python3Packages.buildPythonApplication {
  pname = "nix-update";
  version = "1.8.0";
  src = ./.;
  pyproject = true;
  buildInputs = [ pkgs.makeWrapper ];
  build-system = [ pkgs.python3Packages.setuptools ];
  nativeBuildInputs = [
    pkgs.nixVersions.stable
    pkgs.nix-prefetch-git
  ];
  nativeCheckInputs = [
    pkgs.python3Packages.pytest
    pkgs.python3Packages.pytest-xdist
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
