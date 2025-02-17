{
  rustPlatform,
  fetchCrate,
  hello,
  nix-update-script,
}:
rustPlatform.buildRustPackage rec {
  pname = "fd-find";
  version = "8.0.0";

  src = fetchCrate {
    inherit pname version;
    sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  cargoHash = "sha256-BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=";

  passthru.tests = {
    foo = hello;
    bar = hello;
  };
  passthru.updateScript = nix-update-script {
    attrPath = "crate";
    extraArgs = [
      "--flake"
    ];
  };
}
