{ rustPlatform, fetchFromGitHub }:

rustPlatform.buildRustPackage rec {
  pname = "cntr";
  version = "1.4.0";

  src = fetchFromGitHub {
    owner = "Mic92";
    repo = "cntr";
    rev = version;
    hash = "sha256-rIDAPtDMth/5S+zwTk1tN5BQzFdv7Qq3yNe9wBGnrkk=";
  };

  cargoLock.lockFile = ./Cargo.lock;
}
