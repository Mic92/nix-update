{
  stdenvNoCC,
  fetchurl,
}:

stdenvNoCC.mkDerivation rec {
  pname = "net-news-wire";
  version = "6.1.5";

  src = fetchurl {
    url = "https://github.com/Ranchero-Software/NetNewsWire/releases/download/mac-${version}/NetNewsWire${version}.zip";
    hash = "sha256-92hsVSEpa661qhebeSd5lxt8MtIJRn7YZyKlMs0vle0=";
  };
}
