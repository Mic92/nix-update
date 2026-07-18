{
  buildNpmPackage,
  fetchFromGitHub,
  pnpm_10,
}:

buildNpmPackage rec {
  pname = "flood";
  version = "4.9.2";

  src = fetchFromGitHub {
    owner = "jesec";
    repo = "flood";
    rev = "v${version}";
    hash = "sha256-sIwXx9DA+vRW4pf6jyqcsla0khh8fdpvVTZ5pLrUhhc=";
  };

  npmConfigHook = pnpm_10.configHook;
  npmDeps = pnpmDeps;
  pnpmDeps = pnpm_10.fetchDeps {
    inherit pname version src;
    fetcherVersion = 4;
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
