{
  stdenvNoCC,
  yarn-berry,
}:
stdenvNoCC.mkDerivation (finalAttrs: {
  pname = "yarn-berry-missing-hashes";
  version = "0";

  src = ./.;

  missingHashes = ./missing-hashes.json;
  yarnOfflineCache = yarn-berry.fetchYarnBerryDeps {
    inherit (finalAttrs) src missingHashes;
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
})
