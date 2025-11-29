{
  lib,
  stdenvNoCC,
  bun,
  fetchFromGitHub,
  writableTmpDirAsHomeHook,
}:
let
  pname = "models-dev";
  version = "0-unstable-2025-11-28";
  src = fetchFromGitHub {
    owner = "sst";
    repo = "models.dev";
    rev = "48358b91b776d0bd34cbbc4c70e7ac5ce827b916";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    postFetch = lib.optionalString stdenvNoCC.hostPlatform.isLinux ''
      # NOTE: Normalize case-sensitive directory names that cause issues on case-insensitive filesystems
      cp -r "$out/providers/poe/models/openai"/* "$out/providers/poe/models/openAi/"
      rm -rf "$out/providers/poe/models/openai"
    '';
  };

  node_modules = stdenvNoCC.mkDerivation {
    pname = "${pname}-node_modules";
    inherit version src;

    impureEnvVars = lib.fetchers.proxyImpureEnvVars ++ [
      "GIT_PROXY_COMMAND"
      "SOCKS_SERVER"
    ];

    nativeBuildInputs = [
      bun
      writableTmpDirAsHomeHook
    ];

    dontConfigure = true;

    buildPhase = ''
      runHook preBuild

       export BUN_INSTALL_CACHE_DIR=$(mktemp -d)

       bun install \
         --filter=./packages/web \
         --force \
         --frozen-lockfile \
         --ignore-scripts \
         --no-progress \
         --production

      runHook postBuild
    '';

    installPhase = ''
      runHook preInstall

      mkdir -p $out
      find . -type d -name node_modules -exec cp -R --parents {} $out \;

      runHook postInstall
    '';

    # NOTE: Required else we get errors that our fixed-output derivation references store paths
    dontFixup = true;

    outputHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    outputHashAlgo = "sha256";
    outputHashMode = "recursive";
  };
in
stdenvNoCC.mkDerivation (_finalAttrs: {
  inherit
    pname
    version
    src
    node_modules
    ;

  nativeBuildInputs = [ bun ];

  configurePhase = ''
    runHook preConfigure

    cp -R ${node_modules}/. .

    runHook postConfigure
  '';

  buildPhase = ''
    runHook preBuild

    cd packages/web
    bun run ./script/build.ts

    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall

    mkdir -p $out/dist
    cp -R ./dist $out

    runHook postInstall
  '';
})
