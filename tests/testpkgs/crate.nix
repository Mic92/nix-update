{ rustPlatform, fetchCrate }:

rustPlatform.buildRustPackage rec {
  pname = "fd-find";
  version = "8.0.0";

  src = fetchCrate {
    inherit pname version;
    sha256 = "";
  };

  cargoSha256 = "";
}
