{ beamPackages, fetchFromGitHub }:

beamPackages.mixRelease rec {
  pname = "credo-language-server";
  version = "0.2.0";

  src = fetchFromGitHub {
    owner = "elixir-tools";
    repo = "credo-language-server";
    rev = "refs/tags/v${version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  mixFodDeps = beamPackages.fetchMixDeps {
    inherit pname version src;
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
