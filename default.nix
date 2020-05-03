{ pkgs ?  import <nixpkgs> {} }:


with pkgs;
python3.pkgs.buildPythonApplication rec {
  name = "nix-update";
  src = ./.;
  buildInputs = [ makeWrapper ];
  checkInputs = [ mypy python3.pkgs.black python3.pkgs.flake8 glibcLocales ];
  checkPhase = ''
    echo -e "\x1b[32m## run black\x1b[0m"
    LC_ALL=en_US.utf-8 black --check .
    echo -e "\x1b[32m## run flake8\x1b[0m"
    flake8 nix_update
    echo -e "\x1b[32m## run mypy\x1b[0m"
    mypy --strict nix_update
  '';
  makeWrapperArgs = [
    "--prefix PATH" ":" (lib.makeBinPath [ nix nix-prefetch ])
  ];
  shellHook = ''
    # workaround because `python setup.py develop` breaks for me
  '';

  passthru.env = buildEnv { inherit name; paths = buildInputs ++ checkInputs; };
}
