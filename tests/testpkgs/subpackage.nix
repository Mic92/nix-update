{
  buildGoModule,
  fetchFromGitHub,
  stdenvNoCC,
  nodejs,
  pnpm_9,
  typescript,
}:

let
  pname = "autobrr";
  version = "1.53.0";
  src = fetchFromGitHub {
    owner = "autobrr";
    repo = "autobrr";
    rev = "v${version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  autobrr-web = stdenvNoCC.mkDerivation {
    pname = "${pname}-web";
    inherit src version;

    nativeBuildInputs = [
      nodejs
      pnpm_9.configHook
      typescript
    ];

    sourceRoot = "${src.name}/web";

    pnpmDeps = pnpm_9.fetchDeps {
      inherit (autobrr-web)
        pname
        version
        src
        sourceRoot
        ;
      fetcherVersion = 2;
      hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    };

    postBuild = ''
      pnpm run build
    '';

    installPhase = ''
      cp -r dist $out
    '';
  };
in
buildGoModule rec {
  inherit
    autobrr-web
    pname
    version
    src
    ;

  vendorHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";

  preBuild = ''
    cp -r ${autobrr-web}/* web/dist
  '';
}
