{ fetchFromGitHub
, pnpm_8
, stdenv
}:

stdenv.mkDerivation rec {
  pname = "vesktop";
  version = "1.5.1";

  src = fetchFromGitHub {
    owner = "Vencord";
    repo = "Vesktop";
    rev = "v${version}";
    sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  pnpmDeps = pnpm_8.fetchDeps {
    inherit pname version src;
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
