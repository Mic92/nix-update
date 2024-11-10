{ stdenv, fetchFromGitHub }:
{
  fd = stdenv.mkDerivation rec {
    pname = "fd";
    version = "0.0.0";

    src = fetchFromGitHub {
      owner = "sharkdp";
      repo = pname;
      rev = "v${version}";
      sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    };
  };

  skim = stdenv.mkDerivation rec {
    pname = "skim";
    version = "0.0.0";

    src = fetchFromGitHub {
      owner = "skim-rs";
      repo = pname;
      rev = "v${version}";
      sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    };
  };
}
