{ rustPlatform, fetchFromGitHub }:

rustPlatform.buildRustPackage rec {
  pname = "nurl";
  version = "0.3.7";

  src = fetchFromGitHub {
    owner = "nix-community";
    repo = "nurl";
    rev = "v${version}";
    hash = "sha256-TtH0sfWFWe3oYK/8jJslqjrEY5rR7HGAVDD5iQ2+spY=";
  };

  cargoLock.lockFile = ./Cargo.lock;
}
