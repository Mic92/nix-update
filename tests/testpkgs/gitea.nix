{ stdenv, fetchFromGitea }:

stdenv.mkDerivation rec {
  pname = "nsxiv";
  version = "29";

  src = fetchFromGitea {
    domain = "codeberg.org";
    owner = "nsxiv";
    repo = "nsxiv";
    rev = "v${version}";
    hash = "sha256-swzTdQ6ow1At4bKRORqz6fb0Ej92yU9rlI/OgcinPu4=";
  };
}
