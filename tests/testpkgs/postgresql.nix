{ fetchFromGitHub, stdenv }:

stdenv.mkDerivation rec {
  pname = "postgresql";
  version = "17.0";

  src = fetchFromGitHub {
    owner = "postgres";
    repo = "postgres";
    tag = "REL_${builtins.replaceStrings [ "." ] [ "_" ] version}";
    sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
