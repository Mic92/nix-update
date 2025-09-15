{
  buildNpmPackage,
  fetchFromGitHub,
  pnpm_9,
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

  npmConfigHook = pnpm_9.configHook;
  npmDeps = pnpmDeps;
  pnpmDeps = pnpm_9.fetchDeps {
    inherit pname version src;
    fetcherVersion = 2;
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
