{
  stdenv,
  writeShellScript,
}:

stdenv.mkDerivation {
  pname = "non-flake-update-script";
  version = "1.0.0";

  src = ./.;

  # A custom update script as an out-of-nixpkgs repo might ship it: it runs
  # from the repo root and receives UPDATE_NIX_* from nix-update.
  passthru.updateScript = writeShellScript "update-non-flake-update-script" ''
    set -eu
    sed -i "s/version = \"$UPDATE_NIX_OLD_VERSION\";/version = \"1.2.3\";/" non-flake-update-script.nix
  '';
}
