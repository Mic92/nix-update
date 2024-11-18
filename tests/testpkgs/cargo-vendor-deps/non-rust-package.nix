{
  stdenv,
  rustPlatform,
  fetchFromGitHub,
}:
stdenv.mkDerivation rec {
  pname = "popsicle";
  version = "1.3.0";

  src = fetchFromGitHub {
    owner = "pop-os";
    repo = "popsicle";
    rev = version;
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  nativeBuildInputs = [
    rustPlatform.bindgenHook
    rustPlatform.cargoSetupHook
  ];

  cargoDeps = rustPlatform.fetchCargoVendor {
    inherit pname version src;
    hash = "sha256-BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=";
  };
}
