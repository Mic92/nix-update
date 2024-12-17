{
  buildNpmPackage,
  fetchFromGitHub,
}:

buildNpmPackage rec {
  pname = "emmet-language-server";
  version = "2.5.0";

  src = fetchFromGitHub {
    owner = "olrtg";
    repo = "emmet-language-server";
    rev = "v${version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  npmDepsHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";

  postPatch = ''
    cp ${./package-lock.json} ./package-lock.json
  '';

}
