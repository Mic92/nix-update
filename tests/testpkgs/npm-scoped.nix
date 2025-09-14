{ stdenv, fetchurl }:

stdenv.mkDerivation rec {
  pname = "nanocoder";
  version = "1.10.2";

  src = fetchurl {
    url = "https://registry.npmjs.org/@motesoftware/nanocoder/-/nanocoder-${version}.tgz";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
