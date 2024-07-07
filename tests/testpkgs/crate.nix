{
  rustPlatform,
  fetchCrate,
  hello,
}:

rustPlatform.buildRustPackage rec {
  pname = "fd-find";
  version = "8.0.0";

  src = fetchCrate {
    inherit pname version;
    sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  cargoSha256 = "sha256-BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=";

  passthru.tests = {
    foo = hello;
    bar = hello;
  };
}
