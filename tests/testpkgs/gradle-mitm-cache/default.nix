{
  stdenv,
  fetchFromGitHub,
  gradle,
}:

stdenv.mkDerivation rec {
  pname = "armitage";
  version = "unstable-2022-12-05";

  src = fetchFromGitHub {
    owner = "r00t0v3rr1d3";
    repo = "armitage";
    rev = "c470e52773de4b44427ed4894c4096a44684b7e5";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  mitmCache = gradle.fetchDeps {
    inherit pname;
    data = ./deps.json;
  };
}
