{ python3Packages
, rustPlatform
, fetchFromGitHub
,
}:

python3Packages.buildPythonPackage rec {
  pname = "lancedb";
  version = "0.11.0";

  src = fetchFromGitHub {
    owner = "lancedb";
    repo = "lancedb";
    rev = "python-v${version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  cargoDeps = rustPlatform.importCargoLock { lockFile = ./Cargo.lock; };
}
