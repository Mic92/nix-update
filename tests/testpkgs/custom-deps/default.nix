{
  stdenvNoCC,
  fetchYarnDeps,
  fetchPnpmDeps,
}:
stdenvNoCC.mkDerivation (finalAttrs: {
  pname = "custom-deps";
  version = "0";

  src = ./.;

  yarnOfflineCacheCustom = fetchYarnDeps {
    name = "yarn-custom-deps";
    yarnLock = ./yarn/yarn.lock;
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  pnpmDepsCustom = fetchPnpmDeps {
    inherit (finalAttrs) version;
    pname = "pnpm-custom-deps";
    src = ./pnpm;
    fetcherVersion = 1;
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  buildCommand = "touch $out";
})
