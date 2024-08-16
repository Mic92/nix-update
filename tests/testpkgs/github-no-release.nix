{ stdenv, fetchFromGitHub }:

stdenv.mkDerivation rec {
  pname = "proton-vpn";
  version = "4.3.2";

  src = fetchFromGitHub {
    owner = "ProtonVPN";
    repo = "${pname}-gtk-app";
    rev = "v${version}";
    sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
