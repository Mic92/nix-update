{
  python3Packages,
  rustPlatform,
  fetchFromGitHub,
}:

python3Packages.buildPythonPackage rec {
  pname = "pycrdt";
  version = "0.9.6";

  src = fetchFromGitHub {
    owner = "jupyter-server";
    repo = "pycrdt";
    rev = "v${version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  nativeBuildInputs = [
    rustPlatform.cargoSetupHook
    rustPlatform.maturinBuildHook
  ];

  cargoDeps = rustPlatform.importCargoLock { lockFile = ./Cargo.lock; };
}
