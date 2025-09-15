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

  cargoHash = "sha256-BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=";
}
