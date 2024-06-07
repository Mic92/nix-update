{ stdenv, fetchurl }:

stdenv.mkDerivation rec {
  pname = "pnpm";
  version = "9.1.3";

  src = fetchurl {
    url = "https://registry.npmjs.org/pnpm/-/pnpm-${version}.tgz";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
}
