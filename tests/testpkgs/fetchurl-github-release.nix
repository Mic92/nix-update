{
  stdenv,
  fetchurl,
}:

stdenv.mkDerivation (finalAttrs: {
  version = "5.0.5";
  pname = "adminer";

  src = fetchurl {
    url = "https://github.com/vrana/adminer/releases/download/v${finalAttrs.version}/adminer-${finalAttrs.version}.zip";
    hash = "sha256-7VAy9bE9dUZpkKtRMUa/boA6NlfZ7tBT/2x1POtazoM=";
  };
})
