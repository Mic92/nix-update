{ stdenv, fetchFromGitLab }:

stdenv.mkDerivation rec {
  pname = "phosh";
  version = "0.20.0";

  src = fetchFromGitLab {
    domain = "gitlab.gnome.org";
    group = "world";
    owner = "phosh";
    repo = pname;
    rev = "v${version}";
    sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
