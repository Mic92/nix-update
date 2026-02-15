{ stdenv, fetchFromGitLab }:

stdenv.mkDerivation rec {
  pname = "caps2esc";
  version = "0.1.3";

  src = fetchFromGitLab {
    group = "interception";
    owner = "linux/plugins";
    repo = pname;
    rev = "v${version}";
    sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
