{
  bun,
  buildNpmPackage,
  fetchFromGitHub,
}:
buildNpmPackage rec {
  pname = "goofcord";
  version = "2.0.1";

  src = fetchFromGitHub {
    owner = "Milkshiift";
    repo = "Goofcord";
    tag = "v${version}";
    hash = "sha256-c/NDju5K4DnKLZjE0ZD0TSpm5YWhZUXGmZs/AJhF7Jk=";
  };

  npmConfigHook = bun.configHook;
  npmHash = bunDeps;
  bunDeps = bun.fetchDeps {
    inherit
      pname
      src
      version
      ;
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
