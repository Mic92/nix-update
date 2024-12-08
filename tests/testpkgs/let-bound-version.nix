{ stdenv, fetchFromGitHub }:

let
  version = "8.0.0";
in
stdenv.mkDerivation rec {
  pname = "fd";
  inherit version;

  src = fetchFromGitHub {
    owner = "sharkdp";
    repo = pname;
    rev = "v${version}";
    sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
