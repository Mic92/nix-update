{
  rustPlatform,
  fetchFromGitHub,
}:
rustPlatform.buildRustPackage rec {
  pname = "ruff";
  version = "0.7.0";

  src = fetchFromGitHub {
    owner = "astral-sh";
    repo = pname;
    rev = version;
    hash = "sha256-+8JKzKKWPQEanU2mh8p5sRjnoU6DawTQQi43qRXVXIg=";
  };

  cargoLock = {
    lockFile = src + "/Cargo.lock";
    outputHashes = {
      "lsp-types-0.95.1" = "sha256-8Oh299exWXVi6A39pALOISNfp8XBya8z+KT/Z7suRxQ=";
      "salsa-0.18.0" = "sha256-vuLgeaqIL8U+5PUHJaGdovHFapAMGGQ9nPAMJJnxz/o=";
    };
  };
}
