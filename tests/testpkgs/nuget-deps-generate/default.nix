{
  buildDotnetModule,
  fetchFromGitHub,
}:

buildDotnetModule rec {
  pname = "celeste64";
  version = "1.1.0";

  src = fetchFromGitHub {
    owner = "ExOK";
    repo = "Celeste64";
    tag = "v${version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  nugetDeps = ./deps.json;
}
