{ python3Packages
, rustPlatform
, fetchFromGitHub
}:

python3Packages.buildPythonPackage rec {
  pname = "pylance";
  version = "0.15.0";

  src = fetchFromGitHub {
    owner = "lancedb";
    repo = "lance";
    rev = "v${version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  nativeBuildInputs = [
    rustPlatform.cargoSetupHook
    rustPlatform.maturinBuildHook
  ];

  cargoDeps = rustPlatform.importCargoLock { lockFile = ./Cargo.lock; };
}
